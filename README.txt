CADENCE // DEADZONE — FINAL SUBMISSION

PROJECT SUMMARY
CADENCE // DEADZONE is a fully autonomous top-down zombie-survival game.
There is no human-controlled player. Cadence is the only player and uses the
official Cadence Brain to select high-level combat behavior while the game
provides observations, executes actions, measures outcomes, and returns rewards.

The goal of the project is to make learning visible in a game environment:
Cadence survives repeated runs, receives feedback from its own actions, saves
its learned state, and continues improving across launches.

HOW CADENCE LEARNS
1. The game builds a compact observation of the current situation.
2. The official Cadence Brain selects one of seven tactical actions.
3. The environment executes that action.
4. The game measures what happened.
5. The resulting reward is fed back to Cadence on the next step.
6. Cadence's checkpoint is saved and restored so learning continues between runs.

OBSERVATIONS
- Current health
- Nearest-enemy pressure / distance
- Horde pressure
- Medkit availability / proximity
- Special-weapon availability / proximity

LEARNED HIGH-LEVEL ACTIONS
- KITE
- STRAFE_LEFT
- STRAFE_RIGHT
- CHASE
- HOLD
- SEEK_HEALTH
- SEEK_WEAPON

REWARD SIGNALS
Positive:
- Damaging enemies
- Killing enemies
- Useful health pickups
- Useful weapon pickups
- Clearing areas

Negative:
- Taking damage
- Invalid / ineffective pickup choices
- Death

DETERMINISTIC BODY / SAFETY LAYER
These systems are intentionally separated from the learned tactical policy:
- A* pathfinding around solid map objects
- Automatic unstuck recovery
- Mandatory low-health medkit behavior
- Boss-charge dodge reflex
- Corner-escape reflex

This separation lets Cadence learn strategic decisions while a reliable body
controller handles basic navigation and emergency survival.

PERSISTENT TRAINING FILES
- cadence_deadzone_official_brain_v2.npz
  Main learned Cadence checkpoint.

- cadence_deadzone_official_brain_v2_backup.npz
  Automatic backup of the learned checkpoint.

- cadence_training_stats.json
  Persistent run statistics used to show improvement over time.

TRAINING TELEMETRY
The in-game HUD displays:
- Current run
- Survival time
- Average survival time
- Best area
- Best score
- Total area clears

LOCAL TEST RESULT
During development testing, Cadence reached Level 7 within 7 autonomous runs
and continued to show visible improvement in survival behavior.

REQUIREMENTS
- Python 3.13+
- pygame 2.6.1
- numpy
- cadence-net 0.74.0

INSTALL
python -m pip install -r requirements.txt

RUN
python game.py

IMPORTANT FOR SUBMISSION
If you want judges to see the already-trained behavior, include your existing:
cadence_deadzone_official_brain_v2.npz

You may also include:
cadence_training_stats.json

Do not replace those two files with empty/new versions before submission.
