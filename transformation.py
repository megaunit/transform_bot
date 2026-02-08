from copy import deepcopy as copy
from manim import *
from manim.utils.paths import straight_path
import numpy as np
import math
import json
import sys
import os
import subprocess

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
        matrix = config.get(str(self.channel_id))
        m = [matrix[:2], matrix[2:]]
        # func = None
        func = lambda x: math.sqrt(x**2-1)
        func = lambda x: abs(x)

        try:
            test_vals = np.linspace(-50, 50, 200)
            [func(x) for x in test_vals] # testing if is defined across space
        except (ValueError, ZeroDivisionError, ArithmeticError, TypeError):
            func = lambda x: np.nan

        plane_scale = 0.6
        plane = NumberPlane(x_range=[-50, 50, 1], y_range=[-50, 50, 1],).scale(plane_scale)
        transformed_plane = copy(plane)
        back_plane = copy(plane).set_color(WHITE).set_opacity(0.2)

        print(matrix)
        
        eq = Tex(rf"$\begin{{bmatrix}}{matrix[0][0]}& {matrix[0][1]}\\{matrix[1][0]} & {matrix[1][1]}\end{{bmatrix}}$"
        # eq = Tex(rf"$\begin{{bmatrix}}{1.0}& {5.0}\\{3.0} & {2.0}\end{{bmatrix}}$"
        # eq = Text(f"{matrix[0][0]}, {matrix[0][1]}\n{matrix[1][0]},{matrix[1][1]}"
        ).shift(UP * 3).shift(LEFT * 5.5)
        det = Rectangle(
            width=plane_scale,
            height=plane_scale,
            stroke_color=YELLOW,
            fill_color=YELLOW,
            fill_opacity=0.1
        ).move_to(plane.c2p(0.5, 0.5))
        det_val = np.linalg.det(matrix)
        det_val = Tex(rf"$det = {round(det_val, 2)}$").next_to(eq, DOWN).scale(0.85).set_color(YELLOW)
        # det_val = Text(rf"det = {round(det_val, 2)}").next_to(eq, DOWN).scale(0.85).set_color(YELLOW)
        
        i = Vector(plane.c2p(1, 0), color=GREEN)
        j = Vector(plane.c2p(0, 1), color=RED)
        
        if func:
            func = plane.plot(func)
        group = VGroup(func, plane, det).move_to(ORIGIN) if func else VGroup(plane, det).move_to(ORIGIN)
        self.add(eq)
        self.add(plane)
        self.add(back_plane)
        self.add(det)
        self.add(i)
        self.add(j)
        self.bring_to_back(plane)
        self.bring_to_back(back_plane)
        transformed_plane.apply_matrix(matrix)
        
        if func:
            self.play(Create(func, run_time=1.5, rate_func=linear))
        self.play(
            j.animate.put_start_and_end_on(j.get_start(), transformed_plane.c2p(0,1)),
            i.animate.put_start_and_end_on(i.get_start(), transformed_plane.c2p(1,0)),
            ReplacementTransform(plane, transformed_plane),
            det.animate.apply_matrix(matrix),
            func.animate.apply_matrix(matrix),
            run_time=3,
            rate_func=smooth,
            path_func=straight_path()
        )
        self.play(Write(det_val), run_time=1.4)
        self.wait(0.5)
        self.wait(1.5)