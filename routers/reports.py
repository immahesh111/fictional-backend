from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from database import get_db
from models import Operator, LoginLog
from schemas import OperatorReport, ReportEntry
from auth import get_current_admin

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{operator_id}", response_model=OperatorReport)
async def get_operator_report(
    operator_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get performance report for an operator
    Requires admin authentication
    """
    # Get operator details
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator with ID {operator_id} not found"
        )
    
    # Get all login logs for this operator
    login_logs = db.query(LoginLog).filter(
        LoginLog.operator_id == operator_id
    ).order_by(LoginLog.login_time.desc()).all()
    
    # Calculate statistics
    total_logins = len(login_logs)
    total_hours = 0.0
    entries = []
    
    for log in login_logs:
        # Calculate duration
        duration_hours = None
        logout_time_str = None
        
        if log.logout_time:
            duration = log.logout_time - log.login_time
            duration_hours = duration.total_seconds() / 3600
            total_hours += duration_hours
            logout_time_str = log.logout_time.strftime("%H:%M:%S")
        
        # Create report entry
        entry = ReportEntry(
            date=log.date,
            shift=log.shift,
            login_time=log.login_time.strftime("%H:%M:%S"),
            logout_time=logout_time_str,
            duration_hours=round(duration_hours, 2) if duration_hours else None
        )
        entries.append(entry)
    
    # Create report
    report = OperatorReport(
        operator_id=operator.operator_id,
        operator_name=operator.name,
        machine_no=operator.machine_no,
        total_logins=total_logins,
        total_hours=round(total_hours, 2),
        entries=entries
    )
    
    return report


@router.get("/{operator_id}/export", response_class=FileResponse)
async def export_operator_report(
    operator_id: str,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Export operator report as PDF
    Requires admin authentication
    """
    # Get operator details
    operator = db.query(Operator).filter(Operator.operator_id == operator_id).first()
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Operator with ID {operator_id} not found"
        )
    
    # Get all login logs for this operator
    login_logs = db.query(LoginLog).filter(
        LoginLog.operator_id == operator_id
    ).order_by(LoginLog.login_time.desc()).all()
    
    # Create PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"<b>Performance Report - {operator.name}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Operator info
    info = Paragraph(f"<b>Operator ID:</b> {operator.operator_id}<br/>"
                     f"<b>Machine No:</b> {operator.machine_no}<br/>"
                     f"<b>Total Logins:</b> {len(login_logs)}<br/>"
                     f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                     styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 20))
    
    # Table data
    table_data = [['Date', 'Shift', 'Login Time', 'Logout Time', 'Duration (hours)']]
    total_hours = 0.0
    
    for log in login_logs:
        logout_time = log.logout_time.strftime("%H:%M:%S") if log.logout_time else "N/A"
        duration = "N/A"
        
        if log.logout_time:
            duration_seconds = (log.logout_time - log.login_time).total_seconds()
            duration_hours = duration_seconds / 3600
            total_hours += duration_hours
            duration = f"{duration_hours:.2f}"
        
        table_data.append([
            log.date,
            log.shift,
            log.login_time.strftime("%H:%M:%S"),
            logout_time,
            duration
        ])
    
    # Add total row
    table_data.append(['', '', '', 'Total Hours:', f"{total_hours:.2f}"])
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightblue),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Save to file
    filename = f"report_{operator_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = f"./uploads/{filename}"
    
    with open(filepath, "wb") as f:
        f.write(buffer.getvalue())
    
    return FileResponse(
        filepath,
        media_type='application/pdf',
        filename=filename
    )
