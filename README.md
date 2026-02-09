# Transform Bot - Linear Transformation Visualizer

A Telegram bot that generates animated visualizations of 2D linear transformations using [Manim Community](https://www.manim.community/). This tool helps students learn linear algebra by visualizing how different functions change under various linear transformations.

## Features

- **Matrix Visualization**: Input any 2x2 matrix to see how it transforms the standard basis vectors ($\hat{i}$ and $\hat{j}$) and the grid.
- **Determinant and Function Plotting**: Visualize how the determinant and different mathematical function (e.g., $f(x) = x^2$) transforms under the given matrix.
- **Interactive**: Simple chat interface to send matrices and commands.

## Installation

1.  **Clone the repository**:

    ```bash
    https://github.com/megaunit/transform_bot.git
    cd transform_bot
    ```

2.  **Create the Conda environment**:
    Use the provided `environment.yml` to set up the environment with all dependencies.

    ```bash
    conda env create -f environment.yml
    conda activate transform-env
    ```

3.  **Bot Token Setup**:
    - Create a new bot on Telegram using [BotFather](https://t.me/BotFather) and get your API token.
    - Paste your token inside `token.txt` file in the root directory

## Usage

1.  **Run the Bot**:
    Start the bot by running the `bot.py` script.

    ```bash
    python bot.py
    ```

2.  **Commands**:
    - /start:
    - **Start**: Brief introduction and usage instructions by using `/start` command
    - **Set Function**: Use `/function <expression>` to set a function to plot (e.g., `/function x**2`). To remove the function, use `/function None`.

  > [!TIP]
  > Follow `SymPy` library notation for functions (it also accept `^` for powers). If no function plots, assume your notation doesn't follow `SymPy`.

    - **Generate Transformation**: Send a 2x2 matrix in the following format:
      ```text
      a b
      c d
      ```
    - The bot will process the matrix and reply with a video animation of the transformation.

3.  **Example**
    - Run this command `/function cos(x)^2 - x/2` to visualize how this function transform with different matrices
    - Send this message to the bot to visualize the shear transformation:

    ```text
    1 1
    0 1
    ```

    - The following video outputs:

https://github.com/user-attachments/assets/5a06376a-36fb-4e11-a10e-0e0002d366e0
