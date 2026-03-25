import os
import importlib
import textwrap
from datetime import datetime
from tkinter import messagebox, filedialog

class ReportLogicHandler:
    """Handles PDF export logic for the Report Management page."""
    
    def __init__(self, page_instance):
        self.page = page_instance

    def export_to_pdf(self):
        if not self.page.current_headings:
            messagebox.showwarning("Export PDF", "Generate a report before exporting.")
            return

        try:
            pagesizes_module = importlib.import_module("reportlab.lib.pagesizes")
            pdfgen_canvas_module = importlib.import_module("reportlab.pdfgen.canvas")
            A4 = pagesizes_module.A4
            Canvas = pdfgen_canvas_module.Canvas
        except ImportError:
            messagebox.showerror(
                "Export PDF",
                "PDF export requires reportlab. Install it with: pip install reportlab",
            )
            return

        safe_title = self.page.current_report_title.replace(" ", "_").replace("-", "_")
        default_name = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = filedialog.asksaveasfilename(
            title="Save Report PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF files", "*.pdf")],
        )
        if not output_path:
            return

        pdf = Canvas(output_path, pagesize=A4)
        page_w, page_h = A4
        left_margin, right_margin, top_margin, bottom_margin = 34, 34, 34, 34
        line_h = 12
        table_width = page_w - left_margin - right_margin
        page_number = 1

        def draw_footer(page_no):
            pdf.setStrokeColorRGB(0.82, 0.84, 0.88)
            pdf.setLineWidth(0.7)
            pdf.line(left_margin, bottom_margin + 9, page_w - right_margin, bottom_margin + 9)
            pdf.setFont("Helvetica", 8)
            pdf.setFillColorRGB(0.35, 0.39, 0.45)
            pdf.drawString(left_margin, bottom_margin - 2, "Paragon Apartments")
            pdf.drawRightString(page_w - right_margin, bottom_margin - 2, f"Page {page_no}")

        def draw_header():
            y_top = page_h - top_margin
            pdf.setFillColorRGB(0.16, 0.41, 0.76)
            pdf.roundRect(left_margin, y_top - 28, table_width, 24, 4, stroke=0, fill=1)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont("Helvetica-Bold", 12)
            pdf.drawString(left_margin + 8, y_top - 21, "Paragon Apartments - Official Report")
            pdf.setFillColorRGB(0.17, 0.2, 0.25)
            pdf.setFont("Helvetica", 9)
            pdf.drawRightString(page_w - right_margin - 8, y_top - 21, datetime.now().strftime("%Y-%m-%d %H:%M"))

            report_y = y_top - 44
            pdf.setFont("Helvetica-Bold", 11)
            pdf.setFillColorRGB(0.12, 0.23, 0.39)
            pdf.drawString(left_margin, report_y, self.page.current_report_title)

            summary_labels = list(self.page.summary_cards.keys())
            summary_values = [self.page.summary_cards[label].cget("text") for label in summary_labels]
            box_gap, box_count = 8, max(1, len(summary_labels))
            box_w, box_h = (table_width - (box_gap * (box_count - 1))) / box_count, 34
            box_y = report_y - 44

            for idx, (label, value) in enumerate(zip(summary_labels, summary_values)):
                x = left_margin + idx * (box_w + box_gap)
                pdf.setFillColorRGB(0.95, 0.97, 1)
                pdf.setStrokeColorRGB(0.74, 0.8, 0.9)
                pdf.roundRect(x, box_y, box_w, box_h, 3, stroke=1, fill=1)
                pdf.setFont("Helvetica-Bold", 8)
                pdf.setFillColorRGB(0.24, 0.32, 0.46)
                pdf.drawString(x + 6, box_y + 22, label)
                pdf.setFont("Helvetica-Bold", 10)
                pdf.setFillColorRGB(0.1, 0.19, 0.33)
                pdf.drawString(x + 6, box_y + 9, str(value))
            return box_y - 14

        def draw_table_header(y_top, column_widths):
            header_h = 18
            pdf.setFillColorRGB(0.2, 0.42, 0.77)
            pdf.rect(left_margin, y_top - header_h, table_width, header_h, fill=1, stroke=0)
            pdf.setFillColorRGB(1, 1, 1)
            pdf.setFont("Helvetica-Bold", 8)
            x = left_margin
            for i, heading in enumerate(self.page.current_headings):
                pdf.drawString(x + 4, y_top - 12, str(heading))
                x += column_widths[i]
            pdf.setStrokeColorRGB(0.82, 0.86, 0.92)
            x = left_margin
            for w in column_widths:
                pdf.line(x, y_top - header_h, x, y_top)
                x += w
            pdf.line(left_margin + table_width, y_top - header_h, left_margin + table_width, y_top)
            pdf.line(left_margin, y_top - header_h, left_margin + table_width, y_top - header_h)
            return y_top - header_h

        def normalize_row(row):
            values = [("" if val is None else str(val)) for val in row]
            while len(values) < len(self.page.current_headings): values.append("")
            return values[: len(self.page.current_headings)]

        content_top = draw_header()
        raw_weights = []
        for idx, heading in enumerate(self.page.current_headings):
            max_len = len(str(heading))
            for row in self.page.current_rows:
                max_len = max(max_len, len(normalize_row(row)[idx]))
            raw_weights.append(max(8, min(36, max_len)))
        total_weight = sum(raw_weights) if raw_weights else 1
        column_widths = [(w / total_weight) * table_width for w in raw_weights]
        y = draw_table_header(content_top, column_widths)
        pdf.setFont("Helvetica", 8)
        pdf.setFillColorRGB(0.14, 0.16, 0.2)

        for row in self.page.current_rows:
            cells = normalize_row(row)
            wrapped_cells, max_lines = [], 1
            for i, cell in enumerate(cells):
                approx_chars = max(6, int(column_widths[i] / 4.6))
                wrapped = textwrap.wrap(cell, width=approx_chars)[:3] or [""]
                wrapped_cells.append(wrapped)
                max_lines = max(max_lines, len(wrapped))
            row_height = (max_lines * line_h) + 6
            if y - row_height < bottom_margin + 18:
                draw_footer(page_number)
                pdf.showPage()
                page_number += 1
                y = draw_table_header(draw_header(), column_widths)
                pdf.setFont("Helvetica", 8)
            pdf.setStrokeColorRGB(0.86, 0.89, 0.94)
            pdf.rect(left_margin, y - row_height, table_width, row_height, fill=0, stroke=1)
            x = left_margin
            for i, lines in enumerate(wrapped_cells):
                if i > 0: pdf.line(x, y - row_height, x, y)
                text_y = y - 10
                for line in lines:
                    pdf.drawString(x + 3, text_y, line)
                    text_y -= line_h
                x += column_widths[i]
            y -= row_height

        draw_footer(page_number)
        pdf.save()
        messagebox.showinfo("Export PDF", f"Report saved:\n{os.path.abspath(output_path)}")
        
        
def create_page(parent, user_info=None):
    from main.report_page import ReportManagementPage

    page = ReportManagementPage(parent, user_info)
    page.frame.on_show = page.on_show
    return page.frame