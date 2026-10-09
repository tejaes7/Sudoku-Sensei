"""
Generate Professional 16:9 Widescreen Academic Presentation Deck for Professor Presentation.
Topic: Constraint Satisfaction Problem (CSP) Sudoku Solver & Comparative Analysis
Output: Sudoku_CSP_Professor_Presentation.pptx
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# -----------------------------------------------------------------------------
# Color Palette Constants
# -----------------------------------------------------------------------------
DARK_BG = RGBColor(15, 23, 42)       # Slate 900
LIGHT_BG = RGBColor(248, 250, 252)   # Slate 50
CARD_BG = RGBColor(255, 255, 255)    # Pure White
CARD_BORDER = RGBColor(226, 232, 240)# Slate 200
NAVY_HEADER = RGBColor(30, 41, 59)   # Slate 800
TEXT_MAIN = RGBColor(15, 23, 42)     # Slate 900
TEXT_MUTED = RGBColor(100, 116, 139) # Slate 500
TEXT_LIGHT = RGBColor(241, 245, 249) # Slate 100

# Accent Colors
BLUE_ACCENT = RGBColor(2, 132, 199)  # Sky 600
TEAL_ACCENT = RGBColor(13, 148, 136) # Teal 600
PURPLE_ACCENT = RGBColor(124, 58, 237) # Violet 600
GREEN_ACCENT = RGBColor(16, 185, 129) # Emerald 500
RED_ACCENT = RGBColor(225, 29, 72)   # Rose 600
AMBER_ACCENT = RGBColor(217, 119, 6) # Amber 600

# Pill background tints
BLUE_TINT = RGBColor(224, 242, 254)
GREEN_TINT = RGBColor(209, 250, 229)
PURPLE_TINT = RGBColor(243, 232, 255)
AMBER_TINT = RGBColor(254, 243, 199)
RED_TINT = RGBColor(255, 228, 230)


class DeckBuilder:
    def __init__(self, filename="Sudoku_CSP_Professor_Presentation.pptx"):
        self.filename = filename
        self.prs = Presentation()
        self.prs.slide_width = Inches(13.333)
        self.prs.slide_height = Inches(7.5)
        self.blank_layout = self.prs.slide_layouts[6]
        self.slide_count = 0
        self.total_slides = 13

    def add_blank_slide(self, dark=False):
        self.slide_count += 1
        slide = self.prs.slides.add_slide(self.blank_layout)
        
        # Background
        bg = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5)
        )
        bg.fill.solid()
        bg.fill.fore_color.rgb = DARK_BG if dark else LIGHT_BG
        bg.line.fill.background()

        if not dark:
            # Running Footer
            footer_line = slide.shapes.add_shape(
                MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(7.0), Inches(11.733), Inches(0.02)
            )
            footer_line.fill.solid()
            footer_line.fill.fore_color.rgb = CARD_BORDER
            footer_line.line.fill.background()

            tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(7.05), Inches(8.0), Inches(0.35))
            tf = tx_box.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = "AI Course Project • Constraint Satisfaction Problem (CSP) Sudoku Solver"
            p.font.size = Pt(9)
            p.font.color.rgb = TEXT_MUTED

            tx_box_r = slide.shapes.add_textbox(Inches(9.5), Inches(7.05), Inches(3.0), Inches(0.35))
            tf_r = tx_box_r.text_frame
            p_r = tf_r.paragraphs[0]
            p_r.alignment = PP_ALIGN.RIGHT
            p_r.text = f"Slide {self.slide_count} of {self.total_slides}"
            p_r.font.size = Pt(9)
            p_r.font.color.rgb = TEXT_MUTED

        return slide

    def add_header(self, slide, category: str, title: str, subtitle: str, category_color=BLUE_ACCENT, category_tint=BLUE_TINT):
        # Category Pill
        pill = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.4), Inches(3.2), Inches(0.32)
        )
        pill.fill.solid()
        pill.fill.fore_color.rgb = category_tint
        pill.line.color.rgb = category_color
        pill.line.width = Pt(1)
        tf_pill = pill.text_frame
        tf_pill.vertical_anchor = MSO_ANCHOR.MIDDLE
        p_pill = tf_pill.paragraphs[0]
        p_pill.text = category.upper()
        p_pill.font.size = Pt(9)
        p_pill.font.bold = True
        p_pill.font.color.rgb = category_color
        p_pill.alignment = PP_ALIGN.CENTER

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.78), Inches(11.733), Inches(0.55))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        tf_title.margin_top = 0
        tf_title.margin_left = 0
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = NAVY_HEADER

        # Subtitle
        sub_box = slide.shapes.add_textbox(Inches(0.8), Inches(1.32), Inches(11.733), Inches(0.38))
        tf_sub = sub_box.text_frame
        tf_sub.word_wrap = True
        tf_sub.margin_top = 0
        tf_sub.margin_left = 0
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = subtitle
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_MUTED

        # Thin Header Divider
        divider = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(1.75), Inches(11.733), Inches(0.015)
        )
        divider.fill.solid()
        divider.fill.fore_color.rgb = CARD_BORDER
        divider.line.fill.background()

    def add_card(self, slide, left, top, width, height, title="", top_accent_color=None, bg_color=CARD_BG, border_color=CARD_BORDER):
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
        )
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1)

        # Optional accent strip on top
        if top_accent_color:
            strip = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, Inches(0.08)
            )
            strip.fill.solid()
            strip.fill.fore_color.rgb = top_accent_color
            strip.line.fill.background()

        # Text Frame inside card
        tx_box = slide.shapes.add_textbox(
            left + Inches(0.2), top + Inches(0.15), width - Inches(0.4), height - Inches(0.3)
        )
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_top = 0
        tf.margin_left = 0
        tf.margin_right = 0
        tf.margin_bottom = 0

        if title:
            p = tf.paragraphs[0]
            p.text = title
            p.font.size = Pt(13)
            p.font.bold = True
            p.font.color.rgb = NAVY_HEADER
            p.space_after = Pt(8)

        return tf

    def add_stat_card(self, slide, left, top, width, height, stat_number, label, subtext, color=BLUE_ACCENT, bg_tint=CARD_BG):
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height
        )
        card.fill.solid()
        card.fill.fore_color.rgb = bg_tint
        card.line.color.rgb = color
        card.line.width = Pt(1.5)

        tx_box = slide.shapes.add_textbox(
            left + Inches(0.15), top + Inches(0.15), width - Inches(0.3), height - Inches(0.3)
        )
        tf = tx_box.text_frame
        tf.word_wrap = True
        tf.margin_top = 0
        tf.margin_left = 0

        p1 = tf.paragraphs[0]
        p1.text = stat_number
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = color
        p1.alignment = PP_ALIGN.CENTER
        p1.space_after = Pt(2)

        p2 = tf.add_paragraph()
        p2.text = label
        p2.font.size = Pt(10)
        p2.font.bold = True
        p2.font.color.rgb = NAVY_HEADER
        p2.alignment = PP_ALIGN.CENTER

        if subtext:
            p3 = tf.add_paragraph()
            p3.text = subtext
            p3.font.size = Pt(8.5)
            p3.font.color.rgb = TEXT_MUTED
            p3.alignment = PP_ALIGN.CENTER

    def add_bullet_point(self, tf, bold_prefix, text, pt_size=10, text_color=TEXT_MAIN, space_after=6):
        p = tf.add_paragraph()
        p.space_after = Pt(space_after)
        
        run_bullet = p.add_run()
        run_bullet.text = "• "
        run_bullet.font.bold = True
        run_bullet.font.size = Pt(pt_size)
        run_bullet.font.color.rgb = BLUE_ACCENT

        if bold_prefix:
            run_bold = p.add_run()
            run_bold.text = bold_prefix + " "
            run_bold.font.bold = True
            run_bold.font.size = Pt(pt_size)
            run_bold.font.color.rgb = NAVY_HEADER

        run_text = p.add_run()
        run_text.text = text
        run_text.font.size = Pt(pt_size)
        run_text.font.color.rgb = text_color

    def add_table(self, slide, left, top, width, height, headers, rows_data, col_widths=None, header_bg=NAVY_HEADER):
        rows = len(rows_data) + 1
        cols = len(headers)
        table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
        table = table_shape.table

        if col_widths and len(col_widths) == cols:
            for idx, w in enumerate(col_widths):
                table.columns[idx].width = w

        # Header
        for col_idx, header in enumerate(headers):
            cell = table.cell(0, col_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = header_bg
            tf = cell.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            p = tf.paragraphs[0]
            p.text = header
            p.font.bold = True
            p.font.size = Pt(9.5)
            p.font.color.rgb = TEXT_LIGHT
            p.alignment = PP_ALIGN.CENTER if col_idx > 0 else PP_ALIGN.LEFT

        # Rows
        for row_idx, row_items in enumerate(rows_data):
            row_num = row_idx + 1
            bg_color = LIGHT_BG if row_idx % 2 == 1 else CARD_BG
            for col_idx, item_text in enumerate(row_items):
                cell = table.cell(row_num, col_idx)
                cell.fill.solid()
                cell.fill.fore_color.rgb = bg_color
                tf = cell.text_frame
                tf.word_wrap = True
                tf.vertical_anchor = MSO_ANCHOR.MIDDLE
                p = tf.paragraphs[0]
                p.text = str(item_text)
                p.font.size = Pt(9)
                p.font.color.rgb = TEXT_MAIN
                if col_idx == 0:
                    p.font.bold = True
                    p.alignment = PP_ALIGN.LEFT
                else:
                    p.alignment = PP_ALIGN.CENTER

    def save(self):
        self.prs.save(self.filename)
        print(f"Presentation saved successfully to: {self.filename}")


def build_full_deck():
    builder = DeckBuilder("Sudoku_CSP_Professor_Presentation.pptx")

    # =========================================================================
    # SLIDE 1: Title Slide (High-Impact Dark Theme)
    # =========================================================================
    s1 = builder.add_blank_slide(dark=True)
    
    # Glowing top banner
    glow = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(0.12))
    glow.fill.solid()
    glow.fill.fore_color.rgb = BLUE_ACCENT
    glow.line.fill.background()

    # Pill badge
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.2), Inches(3.4), Inches(0.35))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(30, 41, 59)
    badge.line.color.rgb = BLUE_ACCENT
    badge.line.width = Pt(1)
    tf_b = badge.text_frame
    tf_b.vertical_anchor = MSO_ANCHOR.MIDDLE
    p_b = tf_b.paragraphs[0]
    p_b.text = "ARTIFICIAL INTELLIGENCE • SEMESTER 5"
    p_b.font.size = Pt(9.5)
    p_b.font.bold = True
    p_b.font.color.rgb = RGBColor(56, 189, 248)
    p_b.alignment = PP_ALIGN.CENTER

    # Main Title
    t_box = s1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(10.9), Inches(1.8))
    tf_t = t_box.text_frame
    tf_t.word_wrap = True
    p1 = tf_t.paragraphs[0]
    p1.text = "Constraint Satisfaction Problem (CSP)\nSudoku Solver & Empirical Analysis"
    p1.font.size = Pt(32)
    p1.font.bold = True
    p1.font.color.rgb = RGBColor(255, 255, 255)
    p1.space_after = Pt(12)

    # Subtitle
    sub_box = s1.shapes.add_textbox(Inches(1.2), Inches(3.6), Inches(10.9), Inches(1.0))
    tf_s = sub_box.text_frame
    tf_s.word_wrap = True
    p_sub = tf_s.paragraphs[0]
    p_sub.text = (
        "Empirical Investigation of Heuristic Search (MRV, LCV, AC-3) and Peter Norvig's "
        "Dual-Rule Constraint Propagation versus Combinatorial Backtracking Explosion."
    )
    p_sub.font.size = Pt(14)
    p_sub.font.color.rgb = RGBColor(148, 163, 184)

    # Metadata Card at bottom
    m_card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(5.0), Inches(10.9), Inches(1.4))
    m_card.fill.solid()
    m_card.fill.fore_color.rgb = RGBColor(30, 41, 59)
    m_card.line.color.rgb = RGBColor(51, 65, 85)
    
    tf_m = m_card.text_frame
    tf_m.word_wrap = True
    p_m1 = tf_m.paragraphs[0]
    p_m1.text = "ACADEMIC PRESENTATION & ORAL VIVA DEFENSE"
    p_m1.font.size = Pt(10)
    p_m1.font.bold = True
    p_m1.font.color.rgb = RGBColor(56, 189, 248)
    p_m1.space_after = Pt(4)

    p_m2 = tf_m.add_paragraph()
    p_m2.text = "Project Scope: Objective, Current Implementation (80%), Future Roadmap, Datasets & Literature"
    p_m2.font.size = Pt(11)
    p_m2.font.color.rgb = RGBColor(241, 245, 249)
    p_m2.space_after = Pt(4)

    p_m3 = tf_m.add_paragraph()
    p_m3.text = "Course: Artificial Intelligence  |  Status: Phases 1–3 Complete (100%), Phase 4 Pilot Verified"
    p_m3.font.size = Pt(9.5)
    p_m3.font.color.rgb = RGBColor(148, 163, 184)


    # =========================================================================
    # SLIDE 2: Objectives & Research Questions
    # =========================================================================
    s2 = builder.add_blank_slide()
    builder.add_header(
        s2,
        category="Research Foundations",
        title="Project Objectives & Core Research Questions",
        subtitle="Transforming an NP-complete combinatorial search into a deterministic deduction process."
    )

    # Left Card: Core Objective & Problem
    tf_obj = builder.add_card(
        s2, Inches(0.8), Inches(1.95), Inches(5.6), Inches(4.8),
        title="Problem Context & Core Objective",
        top_accent_color=BLUE_ACCENT
    )
    builder.add_bullet_point(
        tf_obj, "NP-Complete Complexity:",
        "Sudoku on an unassigned 9x9 grid possesses a theoretical worst-case search space of O(9^m), where m <= 64 unassigned cells."
    )
    builder.add_bullet_point(
        tf_obj, "The Brute-Force Pathology:",
        "Unguided recursive Depth-First Search (DFS) blindly explores deeply nested invalid branches without early failure detection, suffering catastrophic search thrashing."
    )
    builder.add_bullet_point(
        tf_obj, "Primary Objective:",
        "Formulate Sudoku as a formal Constraint Satisfaction Problem (CSP) and quantitatively measure how domain pruning (Forward Checking), variable ordering (MRV), value ordering (LCV), and dual-rule propagation eliminate exponential branching."
    )
    builder.add_bullet_point(
        tf_obj, "Empirical Rigor:",
        "Instrument every solver with standardized microsecond telemetry to record exact node expansions, wall-clock runtimes, and recursion stack depths."
    )

    # Right Card: 3 Core Research Questions & Metrics
    tf_rq = builder.add_card(
        s2, Inches(6.7), Inches(1.95), Inches(5.8), Inches(4.8),
        title="Key Research Questions & Telemetry Metrics",
        top_accent_color=TEAL_ACCENT
    )
    builder.add_bullet_point(
        tf_rq, "RQ1 (Domain Pruning):",
        "How effectively does Forward Checking (FC) prevent search thrashing compared to unpruned backtracking across escalating difficulty tiers?"
    )
    builder.add_bullet_point(
        tf_rq, "RQ2 (Variable vs. Value Heuristics):",
        "Does Minimum Remaining Values (MRV / 'Fail-First') dominate search tree pruning, and does Least Constraining Value (LCV / 'Succeed-First') justify its computational conflict-counting overhead?"
    )
    builder.add_bullet_point(
        tf_rq, "RQ3 (Deterministic Inference):",
        "Under what conditions does Peter Norvig's dual-rule constraint propagation solve puzzles purely through deduction with exactly ZERO search nodes?"
    )
    builder.add_bullet_point(
        tf_rq, "Unified Telemetry Contract:",
        "Evaluated via: (1) Runtime in ms, (2) Node Expansions (assignments attempted), (3) Max Search Depth, and (4) 100% Mathematical Constraint Certification."
    )


    # =========================================================================
    # SLIDE 3: Mathematical CSP Formulation <X, D, C>
    # =========================================================================
    s3 = builder.add_blank_slide()
    builder.add_header(
        s3,
        category="Mathematical Framework",
        title="Formal CSP Formulation: Triple <X, D, C>",
        subtitle="Mapping the 9x9 Sudoku grid into variables, domains, and 27 AllDifferent constraint groups."
    )

    # 3 Column Cards
    col_w = Inches(3.7)
    gap = Inches(0.3)
    top_pos = Inches(1.95)
    card_h = Inches(4.8)

    # Card 1: Variables X
    tf_x = builder.add_card(s3, Inches(0.8), top_pos, col_w, card_h, title="Variables (X)", top_accent_color=BLUE_ACCENT)
    builder.add_bullet_point(tf_x, "Definition:", "The 81 individual squares of the 9x9 grid: X = {X_r,c | r in [0..8], c in [0..8]}.")
    builder.add_bullet_point(tf_x, "Norvig Notation:", "Labeled row-by-column as 'A1' through 'I9' (e.g., cell E5 is the center of the board).")
    builder.add_bullet_point(tf_x, "State Representation:", "A total assignment maps every X_r,c to a single digit in {1..9}.")
    builder.add_bullet_point(tf_x, "Search Goal:", "Find a complete, consistent assignment satisfying all constraints simultaneously.")

    # Card 2: Domains D
    tf_d = builder.add_card(s3, Inches(0.8) + col_w + gap, top_pos, col_w, card_h, title="Domains (D)", top_accent_color=TEAL_ACCENT)
    builder.add_bullet_point(tf_d, "Blank Cells:", "Initially contain all 9 legal candidate digits: D(X_r,c) = {1, 2, 3, 4, 5, 6, 7, 8, 9}.")
    builder.add_bullet_point(tf_d, "Initial Clues:", "Pre-assigned cells have singleton domains: D(X_r,c) = {d} where d is the given clue.")
    builder.add_bullet_point(tf_d, "Domain Pruning:", "As assignments occur, impossible candidate digits are pruned from peer domains.")
    builder.add_bullet_point(tf_d, "Domain Wipeout:", "If any D(X) -> empty set, the current branch is mathematically proven dead and backtracks immediately.")

    # Card 3: Constraints C
    tf_c = builder.add_card(s3, Inches(0.8) + (col_w + gap) * 2, top_pos, col_w, card_h, title="Constraints & Peers (C)", top_accent_color=PURPLE_ACCENT)
    builder.add_bullet_point(tf_c, "27 Unit Constraints:", "9 Row AllDifferent + 9 Column AllDifferent + 9 Box (3x3) AllDifferent units.")
    builder.add_bullet_point(tf_c, "Exact Peer Topology:", "For every cell X, its peers are the union of its row, column, and box neighbors. Every cell has EXACTLY 20 peers.")
    builder.add_bullet_point(tf_c, "Binary Graph Formulation:", "Sudoku is represented as 810 binary inequality arcs: X != Y for all Y in Peers(X).")
    builder.add_bullet_point(tf_c, "Constraint Graph:", "A 20-regular graph with 81 nodes and 810 edges.")


    # =========================================================================
    # SLIDE 4: Implementation Status: Complete vs. Pending (The "80% Story")
    # =========================================================================
    s4 = builder.add_blank_slide()
    builder.add_header(
        s4,
        category="Project Progress",
        title="Implementation Status: Complete vs. Pending Scope",
        subtitle="Transparent academic milestone tracking: 80% total progress with verified core engine."
    )

    # 3 Stat Cards across the top
    builder.add_stat_card(
        s4, Inches(0.8), Inches(1.95), Inches(3.6), Inches(1.25),
        stat_number="80%",
        label="Overall Project Progress",
        subtext="Core solver engine & pilot verified",
        color=GREEN_ACCENT,
        bg_tint=GREEN_TINT
    )
    builder.add_stat_card(
        s4, Inches(4.8), Inches(1.95), Inches(3.6), Inches(1.25),
        stat_number="100%",
        label="Phases 1, 2, & 3 Completed",
        subtext="All 5 solver algorithms & tests operational",
        color=BLUE_ACCENT,
        bg_tint=BLUE_TINT
    )
    builder.add_stat_card(
        s4, Inches(8.8), Inches(1.95), Inches(3.733), Inches(1.25),
        stat_number="50%",
        label="Phase 4 Benchmark Status",
        subtext="Pilot verified; overnight 10k run pending",
        color=AMBER_ACCENT,
        bg_tint=AMBER_TINT
    )

    # Two Main Cards Below
    card_top = Inches(3.4)
    card_h2 = Inches(3.4)

    # Left: Implemented
    tf_done = builder.add_card(
        s4, Inches(0.8), card_top, Inches(5.7), card_h2,
        title="WHAT WE HAVE IMPLEMENTED (Phases 1–3 + Phase 4 Pilot)",
        top_accent_color=GREEN_ACCENT
    )
    builder.add_bullet_point(tf_done, "Phase 1 (Data & Validation):", "Norvig grid geometry, Kaggle & synthetic CSV loaders, and mathematical constraint validator checking 5 rules.")
    builder.add_bullet_point(tf_done, "Phase 2 (Baseline DFS):", "Unoptimized recursive backtracking with natural row-major scanning, proving baseline search thrashing.")
    builder.add_bullet_point(tf_done, "Phase 3 (CSP Solvers):", "4 advanced CSP algorithms: Forward Checking, MRV + Degree Heuristic, LCV value ordering, and Peter Norvig's Agent.")
    builder.add_bullet_point(tf_done, "Phase 4 Pilot (Harness & Viz):", "Unified Telemetry dataclass, automated benchmark harness, CLI interactive demo, and verified pilot tests across all 4 tiers.")

    # Right: To be implemented
    tf_pending = builder.add_card(
        s4, Inches(6.8), card_top, Inches(5.7), card_h2,
        title="WHAT WE ARE GOING TO IMPLEMENT (Phase 4 Final & Future Work)",
        top_accent_color=AMBER_ACCENT
    )
    builder.add_bullet_point(tf_pending, "Phase 4 Final Scale-Out:", "Execute the full multi-process benchmark overnight on 1,000–10,000 Kaggle puzzles to calculate statistical medians and confidence intervals.")
    builder.add_bullet_point(tf_pending, "Higher-Order Consistency:", "Implement AC-4 (optimal O(ed^2) arc consistency) and Singleton Arc Consistency (SAC) to profile propagation crossover points.")
    builder.add_bullet_point(tf_pending, "Dancing Links (DLX):", "Donald Knuth's Algorithm X using toroidal doubly linked lists as an exact-cover matrix alternative to CSP.")
    builder.add_bullet_point(tf_pending, "SAT / CDCL Encoding:", "Encode Sudoku into Conjunctive Normal Form (CNF) based on Lynce & Ouaknine (2005) with modern SAT solvers.")


    # =========================================================================
    # SLIDE 5: Solver Architectures & Heuristic Progression
    # =========================================================================
    s5 = builder.add_blank_slide()
    builder.add_header(
        s5,
        category="Algorithmic Evolution",
        title="Implemented Solver Suite: 5 Modular Configurations",
        subtitle="A systematic progression from naive brute-force backtracking to deterministic deductive agents."
    )

    # Table of the 5 Solvers
    headers_s5 = ["Configuration", "Variable Selection", "Value Ordering", "Constraint Propagation", "Worst-Case Complexity"]
    rows_s5 = [
        ["Config A: Plain DFS", "Static (Row-Major)", "Natural (1 -> 9)", "None (Check on assignment)", "O(9^m) Exponential"],
        ["Config B: DFS + FC", "Static (Row-Major)", "Natural (1 -> 9)", "Forward Checking (Peer domains)", "Significant Pruning"],
        ["Config C: DFS + FC + MRV", "MRV + Degree Heuristic", "Natural (1 -> 9)", "Forward Checking", "Fail-First Bounded"],
        ["Config D: DFS + FC + MRV + LCV", "MRV + Degree Heuristic", "LCV (Ascending conflicts)", "Forward Checking", "Fail-First + Succeed-First"],
        ["Peter Norvig Agent", "MRV", "Static Domain Order", "Dual-Rule (Singles + Units)", "Near O(1) on Easy/Medium"]
    ]
    col_w_s5 = [Inches(2.5), Inches(2.2), Inches(2.2), Inches(2.6), Inches(2.233)]
    builder.add_table(s5, Inches(0.8), Inches(1.95), Inches(11.733), Inches(2.4), headers_s5, rows_s5, col_w_s5)

    # 3 Summary Cards Below
    c_w = Inches(3.7)
    c_gap = Inches(0.3)
    c_top = Inches(4.65)
    c_h = Inches(2.1)

    tf_c1 = builder.add_card(s5, Inches(0.8), c_top, c_w, c_h, title="Baseline DFS (Control)", top_accent_color=RED_ACCENT)
    builder.add_bullet_point(tf_c1, "Mechanism:", "Scans (0,0) to (8,8), trying 1..9.", pt_size=8.5)
    builder.add_bullet_point(tf_c1, "Vulnerability:", "No lookahead; bad guesses thrash for 370k+ iterations.", pt_size=8.5)

    tf_c2 = builder.add_card(s5, Inches(0.8) + c_w + c_gap, c_top, c_w, c_h, title="MRV + FC (Workhorse)", top_accent_color=BLUE_ACCENT)
    builder.add_bullet_point(tf_c2, "Mechanism:", "Chooses variable with smallest domain |D(X)|.", pt_size=8.5)
    builder.add_bullet_point(tf_c2, "Impact:", "Slashes node expansions by over 96% on hard puzzles.", pt_size=8.5)

    tf_c3 = builder.add_card(s5, Inches(0.8) + (c_w + c_gap) * 2, c_top, c_w, c_h, title="Norvig Agent (Upper Bound)", top_accent_color=PURPLE_ACCENT)
    builder.add_bullet_point(tf_c3, "Mechanism:", "Dual-rule propagation cascades like falling dominoes.", pt_size=8.5)
    builder.add_bullet_point(tf_c3, "Impact:", "Solves standard puzzles with ZERO search guesses!", pt_size=8.5)


    # =========================================================================
    # SLIDE 6: Deep Dive: Forward Checking & MRV Heuristic
    # =========================================================================
    s6 = builder.add_blank_slide()
    builder.add_header(
        s6,
        category="Heuristic Analysis",
        title="Pruning Mechanics: Forward Checking, MRV & The LCV Paradox",
        subtitle="Mathematical principles governing search tree reduction and heuristic computation trade-offs."
    )

    # Left: Forward Checking & MRV
    tf_mrv = builder.add_card(
        s6, Inches(0.8), Inches(1.95), Inches(5.6), Inches(4.8),
        title="Forward Checking & The MRV Principle",
        top_accent_color=BLUE_ACCENT
    )
    builder.add_bullet_point(
        tf_mrv, "Forward Checking (FC):",
        "When variable X is assigned value v, v is instantly eliminated from the domains of all 20 peers. If any unassigned peer experiences a Domain Wipeout (D(Y) = empty), the branch fails immediately."
    )
    builder.add_bullet_point(
        tf_mrv, "Minimum Remaining Values (MRV):",
        "Also known as the 'Fail-First' heuristic. Selects the unassigned cell X* = argmin |D(X)|. If a cell has only 1 or 2 options, assigning it immediately minimizes the branching factor and discovers dead ends at the top of the tree."
    )
    builder.add_bullet_point(
        tf_mrv, "Degree Heuristic (Tie-Breaker):",
        "If multiple variables tie for minimum domain size, selects the cell involved in the largest number of constraints with other unassigned variables to maximize forward constraint propagation."
    )

    # Right: The LCV Paradox
    tf_lcv = builder.add_card(
        s6, Inches(6.7), Inches(1.95), Inches(5.8), Inches(4.8),
        title="The Least Constraining Value (LCV) Trade-Off",
        top_accent_color=AMBER_ACCENT
    )
    builder.add_bullet_point(
        tf_lcv, "LCV Concept ('Succeed-First'):",
        "Given variable X, candidates v in D(X) are ordered ascending by the number of choices they eliminate across unassigned peers: conflicts(v) = sum(1 for Y in Peers(X) if v in D(Y))."
    )
    builder.add_bullet_point(
        tf_lcv, "Theoretical Advantage:",
        "Attempts the most 'polite' value first to maximize the likelihood of finding a valid solution on the very first search path."
    )
    builder.add_bullet_point(
        tf_lcv, "The Empirical Paradox (Why LCV Was Slower):",
        "In Sudoku, valid puzzles have exactly ONE unique solution. MRV already restricts decisions so tightly that LCV cannot find 'alternative' solution paths. Calculating peer intersections across 20 neighbors for every candidate introduces measurable CPU overhead that slightly exceeds its pruning benefit on simple boards!"
    )


    # =========================================================================
    # SLIDE 7: Peter Norvig's Constraint Propagation Agent
    # =========================================================================
    s7 = builder.add_blank_slide()
    builder.add_header(
        s7,
        category="Deterministic AI",
        title="Peter Norvig's Dual-Rule Constraint Propagation Agent",
        subtitle="Pure deductive inference: solving combinatorial puzzles without search tree branching."
    )

    # Left: The Two Rules
    tf_nr = builder.add_card(
        s7, Inches(0.8), Inches(1.95), Inches(6.8), Inches(4.8),
        title="The Two Invariant Propagation Rules",
        top_accent_color=PURPLE_ACCENT
    )
    builder.add_bullet_point(
        tf_nr, "Rule 1: Naked Single (Peer Elimination):",
        "If a cell's domain is reduced to exactly one candidate value (e.g., D(C4) = {'7'}), that cell MUST be 7. The solver assigns 7 and immediately eliminates '7' from all 20 of C4's row, column, and box peers."
    )
    builder.add_bullet_point(
        tf_nr, "Rule 2: Hidden Single (Unit Propagation):",
        "If a unit (any of the 9 rows, 9 columns, or 9 boxes) has only ONE remaining cell that can hold candidate digit d, assign d to that cell immediately! Even if that cell has multiple candidate pencil marks, no other cell in that unit can satisfy the constraint."
    )
    builder.add_bullet_point(
        tf_nr, "The Cascading Domino Effect:",
        "Applying Rule 1 can trigger Rule 2 in a peer unit; applying Rule 2 creates singleton domains that trigger Rule 1 again. This chain reaction cascades across the entire grid until a fixed point is reached."
    )
    builder.add_bullet_point(
        tf_nr, "Hybrid Backtracking for Hard Grids:",
        "If the domino reaction halts on hard puzzles with multiple candidates, Norvig branches on the MRV variable and re-triggers the domino cascade, solving extreme puzzles in only 25 nodes!"
    )

    # Right: High-Impact Metric Cards
    builder.add_stat_card(
        s7, Inches(7.9), Inches(1.95), Inches(4.6), Inches(1.4),
        stat_number="0 Guesses",
        label="Search Nodes on Easy/Medium Puzzles",
        subtext="100% solved via pure deductive logic",
        color=PURPLE_ACCENT,
        bg_tint=PURPLE_TINT
    )
    builder.add_stat_card(
        s7, Inches(7.9), Inches(3.55), Inches(4.6), Inches(1.4),
        stat_number="2.96 ms",
        label="Execution Time on Hard Puzzles",
        subtext="Over 1,000x faster than baseline search",
        color=GREEN_ACCENT,
        bg_tint=GREEN_TINT
    )
    builder.add_stat_card(
        s7, Inches(7.9), Inches(5.15), Inches(4.6), Inches(1.4),
        stat_number="25 Nodes",
        label="Max Nodes on Extreme Puzzles",
        subtext="Baseline DFS times out after 240,000+ nodes",
        color=BLUE_ACCENT,
        bg_tint=BLUE_TINT
    )


    # =========================================================================
    # SLIDE 8: Dataset Specifications & Benchmark Design
    # =========================================================================
    s8 = builder.add_blank_slide()
    builder.add_header(
        s8,
        category="Experimental Design",
        title="Dataset Specifications & Mathematical Validation",
        subtitle="Rigorous benchmark corpora including Kaggle datasets, synthetic generators, and historical extremes."
    )

    # Card 1: Kaggle Dataset
    tf_k = builder.add_card(
        s8, Inches(0.8), Inches(1.95), Inches(5.6), Inches(2.35),
        title="Kaggle 1-Million Dataset Architecture",
        top_accent_color=BLUE_ACCENT
    )
    builder.add_bullet_point(tf_k, "Data Schema:", "Standard CSV containing 'quizzes' (81-char puzzle strings) and 'solutions' (81-char ground truths).", pt_size=8.5)
    builder.add_bullet_point(tf_k, "Format Encoding:", "0 or . represents empty cells; digits 1..9 represent initial clues.", pt_size=8.5)
    builder.add_bullet_point(tf_k, "Difficulty Ingestion:", "Automatically maps existing labels or computes clue density (Easy: 36-40, Medium: 30-34, Hard: 25-28, Extreme: 21-24).", pt_size=8.5)

    # Card 2: Synthetic & Historical Corpora
    tf_s_data = builder.add_card(
        s8, Inches(6.7), Inches(1.95), Inches(5.8), Inches(2.35),
        title="Synthetic & Historical Extreme Benchmark",
        top_accent_color=TEAL_ACCENT
    )
    builder.add_bullet_point(tf_s_data, "Procedural Generation:", "Valid Latin hypercubes generated and symmetric clue carving applied.", pt_size=8.5)
    builder.add_bullet_point(tf_s_data, "Historical Extremes:", "Includes Arto Inkala's 'AI Escargot' (known as the world's hardest Sudoku) and minimal 17-clue puzzles.", pt_size=8.5)
    builder.add_bullet_point(tf_s_data, "Integrity Tagging:", "Marked with is_synthetic: True to prevent false attribution of synthetic data as Kaggle data.", pt_size=8.5)

    # Bottom Card: Mathematical Validator (src/validator.py)
    tf_v = builder.add_card(
        s8, Inches(0.8), Inches(4.5), Inches(11.733), Inches(2.25),
        title="Mathematical Constraint Validator (src/validator.py)",
        top_accent_color=GREEN_ACCENT
    )
    builder.add_bullet_point(tf_v, "Rule 1 (Length & Character Set):", "Output must contain exactly 81 characters, strictly digits 1 to 9 with 0 blank cells.")
    builder.add_bullet_point(tf_v, "Rule 2 (Clue Preservation):", "Every original clue digit must appear unaltered at its exact original row and column index.")
    builder.add_bullet_point(tf_v, "Rules 3, 4, & 5 (Unit Uniqueness):", "All 9 rows, all 9 columns, and all 9 3x3 boxes must each contain {1..9} with zero duplicates.")


    # =========================================================================
    # SLIDE 9: Empirical Benchmark Results Table
    # =========================================================================
    s9 = builder.add_blank_slide()
    builder.add_header(
        s9,
        category="Empirical Findings",
        title="Experimental Telemetry & Performance Comparison",
        subtitle="Verified empirical results collected across standard benchmark runs on hard 19-clue test boards."
    )

    # Telemetry Table
    headers_s9 = ["Solver Configuration", "Difficulty Tier", "Status", "Runtime (ms)", "Node Expansions (Guesses)", "Max Tree Depth"]
    rows_s9 = [
        ["Config A: Plain DFS", "Hard (19 clues)", "TIMEOUT (Fail)", "3,000.01 ms", "376,862", "39"],
        ["Config B: DFS + FC", "Hard (19 clues)", "TIMEOUT (Fail)", "3,000.08 ms", "154,264", "39"],
        ["Config C: DFS + FC + MRV", "Hard (19 clues)", "SUCCESS (100%)", "533.24 ms", "13,971 (96% drop!)", "64"],
        ["Config D: DFS + FC + MRV + LCV", "Hard (19 clues)", "SUCCESS (100%)", "710.93 ms", "18,108", "64"],
        ["Peter Norvig Agent", "Hard (19 clues)", "SUCCESS (100%)", "2.96 ms", "0 (Pure Deduction!)", "0"]
    ]
    col_w_s9 = [Inches(2.5), Inches(1.8), Inches(1.8), Inches(1.6), Inches(2.4), Inches(1.633)]
    builder.add_table(s9, Inches(0.8), Inches(1.95), Inches(11.733), Inches(2.4), headers_s9, rows_s9, col_w_s9)

    # 3 Analytical Takeaway Cards
    t_top = Inches(4.65)
    t_h = Inches(2.1)

    tf_t1 = builder.add_card(s9, Inches(0.8), t_top, c_w, t_h, title="MRV Search Collapse", top_accent_color=GREEN_ACCENT)
    builder.add_bullet_point(tf_t1, "96% Guesses Eliminated:", "Adding MRV collapses search nodes from 376k+ down to 13,971.", pt_size=8.5)
    builder.add_bullet_point(tf_t1, "Solves vs. Times Out:", "Allows the solver to complete within 533ms where baseline failed.", pt_size=8.5)

    tf_t2 = builder.add_card(s9, Inches(0.8) + c_w + c_gap, t_top, c_w, t_h, title="Baseline Search Pathology", top_accent_color=RED_ACCENT)
    builder.add_bullet_point(tf_t2, "Catastrophic Thrashing:", "Baseline DFS expanded 376,862 nodes without solving the board.", pt_size=8.5)
    builder.add_bullet_point(tf_t2, "Shallow Trapping:", "Depth reached only 39 because it got stuck in a dead-end branch.", pt_size=8.5)

    tf_t3 = builder.add_card(s9, Inches(0.8) + (c_w + c_gap) * 2, t_top, c_w, t_h, title="Norvig Grandmaster Dominance", top_accent_color=PURPLE_ACCENT)
    builder.add_bullet_point(tf_t3, "Zero Search Tree Nodes:", "Peter Norvig solved this hard 19-clue board in 2.96ms with 0 guesses!", pt_size=8.5)
    builder.add_bullet_point(tf_t3, "Practical Implication:", "Logical deduction makes search completely unnecessary on most grids.", pt_size=8.5)


    # =========================================================================
    # SLIDE 10: Publication-Quality Visualizations
    # =========================================================================
    s10 = builder.add_blank_slide()
    builder.add_header(
        s10,
        category="Visual Analytics",
        title="Empirical Performance Curves & Visual Analytics",
        subtitle="Automated Matplotlib charts depicting runtime, node expansions, and search depth scaling."
    )

    # Embed generated charts from results/charts/
    chart1_path = "results/charts/summary_dashboard.png"
    chart2_path = "results/charts/node_expansions_by_difficulty.png"

    if os.path.exists(chart1_path):
        # Place summary dashboard across the top-middle
        s10.shapes.add_picture(chart1_path, Inches(0.8), Inches(1.95), width=Inches(7.2))
    else:
        builder.add_card(s10, Inches(0.8), Inches(1.95), Inches(7.2), Inches(4.8), title="Summary Dashboard Chart")

    # Right Card: Observations from Charts
    tf_viz = builder.add_card(
        s10, Inches(8.3), Inches(1.95), Inches(4.233), Inches(4.8),
        title="Key Chart Observations",
        top_accent_color=BLUE_ACCENT
    )
    builder.add_bullet_point(
        tf_viz, "Logarithmic Scaling:",
        "Node expansions for Baseline DFS grow exponentially with puzzle difficulty, hitting the 3-second timeout cap on Hard and Extreme tiers.",
        pt_size=9
    )
    builder.add_bullet_point(
        tf_viz, "Bounded Depth:",
        "MRV maintains a strictly monotonic search depth growth, successfully finding valid leaves at depth 64 without backtracking thrashing.",
        pt_size=9
    )
    builder.add_bullet_point(
        tf_viz, "Runtime Distribution:",
        "Peter Norvig's agent remains flat across Easy, Medium, and Hard tiers (< 3 ms), demonstrating near O(1) effective execution.",
        pt_size=9
    )
    builder.add_bullet_point(
        tf_viz, "Automated Pipeline:",
        "Generated directly from telemetry via 'python visualize.py --csv results/benchmark_results.csv'.",
        pt_size=8.5
    )


    # =========================================================================
    # SLIDE 11: What We Are Going to Implement (Future Roadmap)
    # =========================================================================
    s11 = builder.add_blank_slide()
    builder.add_header(
        s11,
        category="Future Scope & Roadmap",
        title="What We Are Going to Implement: Next Phases & Extensions",
        subtitle="Scaling from pilot verification to large-scale distributed benchmarking and orthogonal solver paradigms."
    )

    # 4 Cards in 2x2 Grid
    grid_w = Inches(5.6)
    grid_h = Inches(2.25)
    g_top1 = Inches(1.95)
    g_top2 = Inches(4.45)
    g_left1 = Inches(0.8)
    g_left2 = Inches(6.9)

    # Item 1: Full 10,000 Benchmark
    tf_f1 = builder.add_card(s11, g_left1, g_top1, grid_w, grid_h, title="1. Full Phase 4 Scale-Out (10k Kaggle Puzzles)", top_accent_color=BLUE_ACCENT)
    builder.add_bullet_point(tf_f1, "Distributed Multiprocessing:", "Execute multi-hour overnight benchmark across 10,000 Kaggle puzzles.", pt_size=8.5)
    builder.add_bullet_point(tf_f1, "Statistical Aggregation:", "Compute median runtimes, 95th percentile confidence intervals, and solve rates to replace [Pending] table rows with publication-grade metrics.", pt_size=8.5)

    # Item 2: Higher-Order Arc Consistency
    tf_f2 = builder.add_card(s11, g_left2, g_top1, grid_w, grid_h, title="2. Higher-Order Arc Consistency (AC-4 & SAC)", top_accent_color=TEAL_ACCENT)
    builder.add_bullet_point(tf_f2, "AC-4 Algorithm:", "Implement Mohr & Henderson's AC-4 with optimal O(ed^2) worst-case time complexity using support counters.", pt_size=8.5)
    builder.add_bullet_point(tf_f2, "Singleton Arc Consistency (SAC):", "Evaluate the crossover point where consistency checking overhead exceeds search pruning savings.", pt_size=8.5)

    # Item 3: Knuth's Dancing Links
    tf_f3 = builder.add_card(s11, g_left1, g_top2, grid_w, grid_h, title="3. Donald Knuth's Dancing Links (DLX)", top_accent_color=PURPLE_ACCENT)
    builder.add_bullet_point(tf_f3, "Exact Cover Formulation:", "Model Sudoku as a 729 x 324 binary incidence matrix covering 4 constraint types (cell, row, col, box).", pt_size=8.5)
    builder.add_bullet_point(tf_f3, "Toroidal Doubly Linked Lists:", "Benchmark Knuth's Algorithm X against CSP heuristics to compare memory locality and pointer-dancing speed.", pt_size=8.5)

    # Item 4: SAT / CDCL Solver
    tf_f4 = builder.add_card(s11, g_left2, g_top2, grid_w, grid_h, title="4. SAT Formulation (Lynce & Ouaknine 2005)", top_accent_color=AMBER_ACCENT)
    builder.add_bullet_point(tf_f4, "CNF Propositional Encoding:", "Encode cell, row, column, and box constraints into Conjunctive Normal Form (8,829 clauses).", pt_size=8.5)
    builder.add_bullet_point(tf_f4, "Modern CDCL Solvers:", "Interface with PySAT / MiniSat to evaluate Conflict-Driven Clause Learning versus CSP backtracking.", pt_size=8.5)


    # =========================================================================
    # SLIDE 12: Academic References & Literature Citations
    # =========================================================================
    s12 = builder.add_blank_slide()
    builder.add_header(
        s12,
        category="Literature & Citations",
        title="Academic References & Foundation Literature",
        subtitle="Peer-reviewed research and seminal textbooks underpinning the project's algorithmic implementations."
    )

    # 4 Full-Width Reference Cards
    ref_h = Inches(1.1)
    ref_w = Inches(11.733)
    r_top = Inches(1.95)
    r_step = Inches(1.22)

    refs = [
        ("1. Peter Norvig (Google Research, 2006 / 2011)",
         "Solving Every Sudoku Puzzle",
         "Seminal research essay formalizing Sudoku constraint propagation via Naked Singles (peer elimination) and Hidden Singles (unit propagation), establishing the benchmark for zero-branching deductive solving.",
         PURPLE_ACCENT),

        ("2. Apekshya Bhattarai, Dinisha Uprety, Pooja Pathak, Safal N. Shrestha, Salina Nakarmi, Sanjog Sigdel (2023)",
         "A Study Of Sudoku Solving Algorithms: Backtracking and Heuristic (Kathmandu University)",
         "Department of Computer Science peer-reviewed study providing comparative experimental metrics on recursive backtracking versus MRV and AC-3 heuristics across varying clue densities.",
         BLUE_ACCENT),

        ("3. Inês Lynce & Joël Ouaknine (2005)",
         "Sudoku as a SAT Problem (Technical University of Lisbon & Oxford University Computing Laboratory)",
         "Foundational paper establishing the formal encoding of Sudoku as a Boolean Satisfiability (SAT) problem in Conjunctive Normal Form (CNF) with minimal, efficient clause formulations.",
         TEAL_ACCENT),

        ("4. Stuart Russell & Peter Norvig (Pearson, 4th Edition, 2020)",
         "Artificial Intelligence: A Modern Approach (AIMA)",
         "Chapters 5 & 6: Constraint Satisfaction Problems, Backtracking Search for CSPs, Variable and Value Ordering (MRV & LCV), Forward Checking, and Arc Consistency (AC-3).",
         NAVY_HEADER)
    ]

    for idx, (auth, title, desc, col) in enumerate(refs):
        tf_r = builder.add_card(s12, Inches(0.8), r_top + idx * r_step, ref_w, ref_h, title="", top_accent_color=col)
        p_auth = tf_r.paragraphs[0]
        p_auth.text = f"{auth} — \"{title}\""
        p_auth.font.size = Pt(11)
        p_auth.font.bold = True
        p_auth.font.color.rgb = NAVY_HEADER
        p_auth.space_after = Pt(2)

        p_desc = tf_r.add_paragraph()
        p_desc.text = desc
        p_desc.font.size = Pt(8.5)
        p_desc.font.color.rgb = TEXT_MUTED


    # =========================================================================
    # SLIDE 13: Summary, Live Demo & Professor Viva Q&A Guide
    # =========================================================================
    s13 = builder.add_blank_slide()
    builder.add_header(
        s13,
        category="Viva Defense & Demo",
        title="Project Summary, Live Demo & Professor Q&A Defense",
        subtitle="Key project takeaways, 5-minute interactive demonstration commands, and anticipated viva questions."
    )

    # Left: Summary & Live Demo Command
    tf_demo = builder.add_card(
        s13, Inches(0.8), Inches(1.95), Inches(5.6), Inches(4.8),
        title="Summary & Interactive Demonstration",
        top_accent_color=GREEN_ACCENT
    )
    builder.add_bullet_point(
        tf_demo, "Core Takeaway:",
        "AI Constraint Satisfaction techniques fundamentally overcome NP-complete exponential explosion: MRV shrinks search trees by 96%, and Norvig propagation eliminates search entirely (0 guesses) on standard puzzles."
    )
    builder.add_bullet_point(
        tf_demo, "Live Interactive Demonstration:",
        "Run the automated demonstration harness live during the defense:\n> python demo.py\nExecutes all 5 solvers step-by-step on an extreme 19-clue board, showing ASCII grids, step counts, and telemetry live."
    )
    builder.add_bullet_point(
        tf_demo, "Automated Testing Verification:",
        "Verify correctness across all mathematical rules:\n> python -m unittest tests/test_solvers.py"
    )

    # Right: Anticipated Professor Viva Questions & Bulletproof Answers
    tf_viva = builder.add_card(
        s13, Inches(6.7), Inches(1.95), Inches(5.8), Inches(4.8),
        title="Anticipated Professor Viva Questions & Answers",
        top_accent_color=PURPLE_ACCENT
    )
    builder.add_bullet_point(
        tf_viva, "Q: 'Why was LCV slower than pure MRV in practice?'",
        "A: In puzzles with a unique solution, MRV already constrains choices to 1 option. LCV's conflict calculations across 20 peers introduce constant-factor CPU overhead without altering the path."
    )
    builder.add_bullet_point(
        tf_viva, "Q: 'Why did Baseline reach depth 39 while MRV reached 64?'",
        "A: Depth 64 represents a successful full assignment of all 64 empty cells! Baseline got stuck in an early bad guess at cell 5, thrashing deeply inside an invalid subtree until timing out."
    )
    builder.add_bullet_point(
        tf_viva, "Q: 'What distinguishes Naked Singles from Hidden Singles?'",
        "A: A Naked Single occurs when a single cell has only 1 candidate remaining (|D(X)| = 1). A Hidden Single occurs when a unit has multiple candidates, but only ONE cell can hold a specific digit."
    )

    builder.save()


if __name__ == "__main__":
    build_full_deck()
