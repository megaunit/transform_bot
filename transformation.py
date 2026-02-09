from copy import deepcopy as copy
from manim import *
from manim.utils.paths import straight_path
import numpy as np
import math
import json
import sys
import os
import subprocess
import sympy as sp
from sympy.calculus.util import continuous_domain

config.tex_template.tex_compiler = "xelatex"
config.tex_template.output_format = ".pdf"
print(f"Using compiler: {config.tex_template.tex_compiler}")

# Monkey-patch convert_to_svg to use pdftocairo (available via poppler)
import manim.utils.tex_file_writing
def convert_to_svg_patched(dvi_file, extension, page=1):
    result = dvi_file.with_suffix(".svg")
    if result.exists(): return result

    if extension != ".pdf":
        raise ValueError(f"Patched convert_to_svg only supports .pdf, got {extension}")

    command = [
        "pdftocairo",
        "-svg",
        "-f", str(page),
        "-l", str(page),
        str(dvi_file),
        str(result)
    ]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not result.exists():
        raise ValueError(f"Failed to convert {dvi_file} to SVG using pdftocairo")
    return result

manim.utils.tex_file_writing.convert_to_svg = convert_to_svg_patched

class Plane(VectorScene):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file_path = os.path.join(script_dir, "config.json")
        self.channel_id = sys.argv[-1]  # Get the channel_id passed from the bot
        
    def construct(self):
        with open(self.config_file_path, "r") as f:
            config = json.load(f)
        user_data = config.get(str(self.channel_id))

        matrix = user_data.get("matrix")
        func_str = user_data.get("function")
        if func_str == "None": func_str = None
        
        # Setup the Plane
        plane_scale = 0.6
        plane = NumberPlane(x_range=[-50, 50, 1], y_range=[-50, 50, 1]).scale(plane_scale)
        transformed_plane = copy(plane)
        back_plane = copy(plane).set_color(WHITE).set_opacity(0.2)
        
        # Prepare the Graph
        func_to_plot, intervals = self.get_plot_data(func_str, min_x=-15, max_x=15)
        
        graphs = VGroup()
        if func_to_plot:
            for start, end in intervals:
                segment = plane.plot(
                    func_to_plot, 
                    x_range=[start, end], 
                    color=ORANGE,
                    use_smoothing=True 
                )
                graphs.add(segment)
        
        # Setup Text & Vectors
        matrix_tex = Tex(rf"$\begin{{bmatrix}}{matrix[0][0]}& {matrix[0][1]}\\{matrix[1][0]} & {matrix[1][1]}\end{{bmatrix}}$")
        matrix_tex.shift(UP * 3, LEFT * 5.5)
        
        det = Rectangle(width=plane_scale, height=plane_scale, stroke_color=YELLOW, fill_color=YELLOW, fill_opacity=0.1)
        det.move_to(plane.c2p(0.5, 0.5))
        
        det_val_num = np.linalg.det(matrix)
        det_val = Tex(rf"$det = {round(det_val_num, 2)}$").next_to(matrix_tex, DOWN).scale(0.85).set_color(YELLOW)
        
        i = Vector(plane.c2p(1, 0), color=GREEN)
        j = Vector(plane.c2p(0, 1), color=RED)
        
        # Add initial objects
        self.add(matrix_tex, plane, back_plane, det, i, j)
        self.bring_to_back(plane, back_plane)
        transformed_plane.apply_matrix(matrix)

        # Draw Graph
        if len(graphs) > 0:
            self.play(Create(graphs), run_time=1.5)
            
        # Animate Transformation
        self.play(
            j.animate.put_start_and_end_on(j.get_start(), transformed_plane.c2p(0,1)),
            i.animate.put_start_and_end_on(i.get_start(), transformed_plane.c2p(1,0)),
            ReplacementTransform(plane, transformed_plane),
            det.animate.apply_matrix(matrix),
            graphs.animate.apply_matrix(matrix), 
            run_time=3,
            rate_func=smooth
        )
        self.play(Write(det_val), run_time=1.4)
        self.wait(2)

    def get_plot_data(self, func_str, min_x=-50, max_x=50):
        if not func_str or func_str == "None":
            return None, []

        try:
            x = sp.Symbol('x', real=True)
            clean_str = func_str.replace("^", "**")
            expr = sp.parse_expr(clean_str)
            
            domain = continuous_domain(expr, x, sp.Interval(min_x, max_x))
            
            valid_intervals = []
            if isinstance(domain, sp.Interval):
                valid_intervals = [domain]
            elif isinstance(domain, sp.Union):
                valid_intervals = list(domain.args)
                
            clean_intervals = []
            for interval in valid_intervals:
                try:
                    start = float(interval.start)
                    end = float(interval.end)
                    # Don't plot tiny dots or backwards ranges
                    if end > start + 0.05: 
                        clean_intervals.append((start, end))
                except (TypeError, ValueError):
                    continue

            f_np = sp.lambdify(x, expr, modules=['numpy'])

            # Define the safe wrapper
            def safe_f(t):
                try:
                    val = f_np(t)
                    if not np.isfinite(val): return np.nan
                    return val.real 
                except:
                    return np.nan

            return safe_f, clean_intervals

        except Exception as e:
            print(f"Error processing function '{func_str}': {e}")
            return None, []