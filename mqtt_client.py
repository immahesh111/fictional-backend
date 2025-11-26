"""
Enhanced MQTT Client with proper error handling and logging
"""
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime
from typing import Optional
from config import settings
import logging

# Create logger for MQTT
logger = logging.getLogger('mqtt')
logger.setLevel(logging.DEBUG if settings.mqtt_debug else logging.INFO)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG if settings.mqtt_debug else logging.INFO)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class MQTTClient:
    """MQTT Client wrapper with HiveMQ Cloud support"""
    
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.connection_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # seconds
        
        logger.info(f"MQTT client initialized for broker: {settings.mqtt_broker}:{settings.mqtt_port}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            self.connection_attempts = 0
            logger.info("✅ Successfully connected to MQTT broker")
            logger.info(f"Connection flags: {flags}")
        else:
            self.connected = False
            error_messages = {
                1: "Connection refused - incorrect protocol version",
                2: "Connection refused - invalid client identifier",
                3: "Connection refused - server unavailable",
                4: "Connection refused - bad username or password",
                5: "Connection refused - not authorized",
            }
            error_msg = error_messages.get(rc, f"Unknown error code: {rc}")
            logger.error(f"❌ Failed to connect to MQTT broker. {error_msg}")
            
            # Provide actionable debugging hints
            if rc == 4:
                logger.error("⚠️  Check your MQTT_USERNAME and MQTT_PASSWORD in .env file")
            elif rc == 5:
                logger.error("⚠️  Check if your HiveMQ Cloud credentials have proper permissions")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.connected = False
        
        if rc == 0:
            logger.info("Disconnected from MQTT broker (intentional)")
        else:
            disconnect_reasons = {
                1: "Incorrect protocol version",
                2: "Invalid client identifier",
                3: "Server unavailable",
                4: "Bad username or password",
                5: "Not authorized",
                6: "Unused",
                7: "Connection lost / Network error",
            }
            reason = disconnect_reasons.get(rc, f"Unknown reason code: {rc}")
            logger.warning(f"⚠️  Unexpected disconnect from MQTT broker. Return code: {rc} ({reason})")
            
            if rc == 7:
                logger.info("Attempting to reconnect...")
                self._reconnect()
    
    def _on_publish(self, client, userdata, mid):
        """Callback when message is published"""
        logger.debug(f"Message published successfully (mid: {mid})")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message is received (for debugging subscriptions)"""
        logger.debug(f"Message received on topic {msg.topic}: {msg.payload.decode()}")
    
    def _reconnect(self):
        """Attempt to reconnect to MQTT broker"""
        while self.connection_attempts < self.max_reconnect_attempts and not self.connected:
            self.connection_attempts += 1
            logger.info(f"Reconnection attempt {self.connection_attempts}/{self.max_reconnect_attempts}...")
            
            try:
                self.client.reconnect()
                time.sleep(1)  # Give it a moment to connect
                
                if self.connected:
                    logger.info("✅ Reconnection successful!")
                    return True
            except Exception as e:
                logger.error(f"Reconnection failed: {e}")
            
            time.sleep(self.reconnect_delay)
        
        if not self.connected:
            logger.error(f"❌ Failed to reconnect after {self.max_reconnect_attempts} attempts")
        
        return self.connected
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            logger.info("Connecting to MQTT broker...")
            logger.debug(f"Broker: {settings.mqtt_broker}")
            logger.debug(f"Port: {settings.mqtt_port}")
            logger.debug(f"Username: {settings.mqtt_username}")
            logger.debug(f"TLS: {settings.mqtt_use_tls}")
            
            # Create client
            self.client = mqtt.Client(
                client_id=f"FastAPI_Backend_{int(time.time())}",
                clean_session=True
            )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            self.client.on_message = self._on_message
            
            # Set username and password if provided
            if settings.mqtt_username and settings.mqtt_password:
                logger.debug("Setting MQTT credentials...")
                self.client.username_pw_set(
                    settings.mqtt_username,
                    settings.mqtt_password
                )
            
            # Configure TLS/SSL if needed
            if settings.mqtt_use_tls:
                logger.debug("Configuring TLS/SSL...")
                self.client.tls_set()
                self.client.tls_insecure_set(True)  # For testing; use proper certs in production
            
            # Connect to broker
            self.client.connect(
                settings.mqtt_broker,
                settings.mqtt_port,
                keepalive=60
            )
            
            # Start network loop in background
            self.client.loop_start()
            
            # Wait a bit for connection
            time.sleep(2)
            
            if not self.connected:
                logger.warning("⚠️  Connection may not be established yet. Messages might fail.")
            
        except Exception as e:
            logger.error(f"❌ Error connecting to MQTT broker: {e}")
            logger.error(f"Please check your MQTT credentials in backend/.env file")
            self.connected = False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            logger.info("Disconnecting from MQTT broker...")
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("✅ MQTT client disconnected")
    
    def publish_unlock_signal(self, machine_no: str, operator_id: str) -> bool:
        """
        Publish unlock signal to specific machine topic
        
        Args:
            machine_no: Machine number (e.g., "M101")
            operator_id: Operator ID who was authenticated
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.connected:
            logger.error("❌ Cannot publish: MQTT client not connected")
            logger.info("Attempting to reconnect...")
            if not self._reconnect():
                return False
        
        try:
            # Construct topic
            topic = f"{settings.mqtt_topic_prefix}/{machine_no}/unlock"
            
            # Create message payload
            message = {
                "action": "unlock",
                "operator_id": operator_id,
                "machine_no": machine_no,
                "timestamp": datetime.now().isoformat()
            }
            
            # Publish message
            logger.info(f"📤 Publishing unlock signal...")
            logger.info(f"   Topic: {topic}")
            logger.info(f"   Payload: {json.dumps(message, indent=2)}")
            
            result = self.client.publish(
                topic,
                json.dumps(message),
                qos=1,  # At least once delivery
                retain=False
            )
            
            # Check if publish was successful
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✅ Unlock signal published successfully!")
                logger.info(f"   Message ID: {result.mid}")
                return True
            else:
                logger.error(f"❌ Failed to publish message. Error code: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error publishing unlock signal: {e}")
            return False

    def publish_lock_signal(self, machine_no: str, operator_id: str) -> bool:
        """
        Publish lock signal to specific machine topic
        
        Args:
            machine_no: Machine number (e.g., "M101")
            operator_id: Operator ID who is logging out
        
        Returns:
            True if published successfully, False otherwise
        """
        if not self.connected:
            logger.error("❌ Cannot publish: MQTT client not connected")
            # Try to reconnect, but don't block too long for logout
            if not self._reconnect():
                return False
        
        try:
            # Construct topic (same topic as unlock, different action)
            topic = f"{settings.mqtt_topic_prefix}/{machine_no}/unlock"
            
            # Create message payload
            message = {
                "action": "lock",
                "operator_id": operator_id,
                "machine_no": machine_no,
                "timestamp": datetime.now().isoformat()
            }
            
            # Publish message
            logger.info(f"🔒 Publishing lock signal...")
            logger.info(f"   Topic: {topic}")
            logger.info(f"   Payload: {json.dumps(message, indent=2)}")
            
            result = self.client.publish(
                topic,
                json.dumps(message),
                qos=1,
                retain=False
            )
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"✅ Lock signal published successfully!")
                return True
            else:
                logger.error(f"❌ Failed to publish lock message. Error code: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error publishing lock signal: {e}")
            return False


# Global MQTT client instance
mqtt_client = MQTTClient()
