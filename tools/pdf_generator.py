
import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

def generate_student_report(nickname, stats, mastery_list, output_path):
    """
    Generate a professional PDF progress report for a student.
    
    :param nickname: Student's nickname
    :param stats: Dict containing streak, total_interactions, badges
    :param mastery_list: List of dicts with topic, category, score
    :param output_path: Where to save the PDF
    """
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Custom Styles
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.hexColor("#2E7D32"), # Udene Green
        spaceAfter=20,
        alignment=1 # Center
    )
    
    subtitle_style = ParagraphStyle(
        'SubtitleStyle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.grey,
        spaceAfter=10
    )

    # 1. Header
    story.append(Paragraph(f"Udene STEM Learning Report", title_style))
    story.append(Paragraph(f"Student: <b>{nickname}</b>", subtitle_style))
    story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 20))

    # 2. Key Stats Summary
    story.append(Paragraph("🏁 Learning Highlights", styles['Heading2']))
    stats_data = [
        ["Daily Streak", f"{stats.get('streak', 0)} Days 🔥"],
        ["Total Interactions", f"{stats.get('total_interactions', 0)}"],
        ["Badges Earned", f"{len(stats.get('badges', []))} Achievements"]
    ]
    t_stats = Table(stats_data, colWidths=[150, 200])
    t_stats.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_stats)
    story.append(Spacer(1, 20))

    # 3. Mastery Progress
    story.append(Paragraph("📚 Mastery Progress", styles['Heading2']))
    if not mastery_list:
        story.append(Paragraph("No mastery data yet. Start a lesson to track progress!", styles['Normal']))
    else:
        # Table Header
        header = ["Topic", "Category", "Mastery %", "Status"]
        table_data = [header]
        
        for m in mastery_list:
            score = m.get('score', 0)
            status = "Mastered" if score >= 85 else "Advancing" if score >= 60 else "Beginner"
            table_data.append([m.get('topic', 'Unknown'), m.get('category', 'general'), f"{score}%", status])

        t_mastery = Table(table_data, colWidths=[150, 100, 100, 100])
        t_mastery.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.hexColor("#2E7D32")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
        ]))
        story.append(t_mastery)

    # 4. Badges Gallery
    story.append(Spacer(1, 20))
    story.append(Paragraph("🏅 Achievement Badges", styles['Heading2']))
    badges = stats.get('badges', [])
    if not badges:
        story.append(Paragraph("Continue learning to unlock badges!", styles['Italic']))
    else:
        badge_text = ", ".join(badges)
        story.append(Paragraph(badge_text, styles['Normal']))

    # 5. Footer
    story.append(Spacer(1, 40))
    story.append(Paragraph("<i>'Impact through learning.' - Udene Physics v2</i>", styles['Normal']))

    doc.build(story)
    return output_path

def generate_hardware_guide(nickname, project_name, data, output_path):
    """Generate a step-by-step hardware build guide PDF."""
    # (Optional future expansion)
    pass
