# Sherlock Claude: AI-Powered Detective Simulation

Sherlock Claude is an interactive detective game that uses AI to simulate a crime-solving experience. The game features an AI investigator that analyzes clues and attempts to solve a mystery, guided by an AI referee.

## What are Detective Games

Detective games are games that put players in the role of a detective. There has been some event 
that requires players to explore, formulate plans, and navigate the fictional world where the 
scenario takes place and piece together a puzzle. Games like SHCD, Detective Hong-Kong, Chronicles
of Crime, and many others are very popular and have a large following on the internet.


## Why make a Bot to solve them.

One of the things that distinguish Detective games from other intelligence puzzles is they are 
mostly framed as puzzles in the *human* world, as opposed to the *physical* world. So factors like
deception, human nature and its failings, theory of mind, creativity, evaluation of empirical 
evidence, puzzle solving, and many other facets that are typically not tested in other chatbot 
tests are readily tested here.

Furthermore, the tests can be done in measurable way. There *is* a solution so you can gauge the 
performance of a chatbot on that solution against known answers and get a numerical score.

And finally, these cases can be quite hard, which means that a metric developed around these 
tests is likely very open-ended, and could be a good way to distinguish between even very 
high level bots.


## slideshow and demo:

- [slideshow part 1](docs/presentation/slideshow.mp4)

- [demo](docs/presentation/slideshow2.mp4)

- [slideshow part 2](docs/presentation/slideshow3.mp4)


## API Structure 

The project is organized into several Python modules:

- `config.py`:        Configuration settings for the API
- `utils.py`:         Utility functions
- `case_loader.py`:   Handles loading and processing of case files
- `claude_bot.py`:    Base class for interacting with the Claude API
- `referee.py`:       Contains the Referee class. Knows the details of the case and delivers clues to the investigator. Judges how good any solution is made by the investigator.
- `investigator.py`:  Contains the Investigator class. Proceeds with the investigation, and returns a potential solution to be judged by the referee.
- `investigation.py`: Manages the overall investigation process

## Requirements

- Python 3.7+
- pip (Python package installer)

## Setup

1. Clone the repository:
   ```
   git clone https://github.com/ed-peschko/sherlock-claude.git
   cd sherlock-claude
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Anthropic API key:
   - Create a `.env` file in the project root directory
   - Add your API key to the file:
     ```
     ANTHROPIC_API_KEY=your_api_key_here
     ```

## Running the Game

To start the game, run:

```
python run_case.py <case_directory>
```

The game will use the case files located in the `cases/sample_case` directory by default. To use a different case, modify the `CASE_DIRECTORY` variable in `config.py`.

## Creating Custom Cases

To create a custom case:

1. Create a new directory under the `cases` folder
2. Add the following JSON files to your case directory:
   - `setup.json`: Initial case setup
   - `clues.json`: List of clues
   - `questions_answers.json`: Questions to be solved and their answers
   - `solution.json`: The solution to the case
   - `special_spots.json`: Special investigation spots

Refer to the `sample_case` for the expected structure of these files.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

You can get a hold of the author at ed.peschko@gmail.com

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

