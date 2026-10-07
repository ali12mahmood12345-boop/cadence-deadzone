import pygame
import sys
import math
import random
import json
import os
import heapq
import shutil
import numpy as np

from cadence import Brain

pygame.init()

# ============================================================
# SETTINGS
# ============================================================

WIDTH = 1920
HEIGHT = 1080
FPS = 60

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("CADENCE // DEADZONE // OFFICIAL CADENCE BRAIN")

clock = pygame.time.Clock()

font_small = pygame.font.SysFont("consolas", 28, bold=True)
font_medium = pygame.font.SysFont("consolas", 36, bold=True)
font_big = pygame.font.SysFont("consolas", 46, bold=True)
font_huge = pygame.font.SysFont("consolas", 76, bold=True)

# ============================================================
# COLORS
# ============================================================

BACKGROUND = (14, 17, 15)

WHITE = (230, 235, 230)
RED = (210, 55, 55)
DARK_RED = (110, 30, 30)
GREEN = (70, 210, 110)
DARK_GREEN = (25, 100, 55)

YELLOW = (255, 215, 90)
ORANGE = (255, 145, 35)
FIRE_RED = (255, 75, 25)
BLUE = (70, 170, 255)

SKIN = (205, 165, 120)

UNIFORM = (74, 103, 66)
UNIFORM_DARK = (46, 67, 42)
HELMET = (52, 74, 47)

GUN = (42, 44, 42)
GUN_LIGHT = (105, 108, 102)

ZOMBIE_SKIN = (91, 128, 74)
ZOMBIE_DARK = (49, 71, 42)
ZOMBIE_SHIRT = (91, 68, 58)

# ============================================================
# ARENA
# ============================================================

ARENA_LEFT = 60
ARENA_TOP = 60
ARENA_RIGHT = WIDTH - 60
ARENA_BOTTOM = HEIGHT - 60

# ============================================================
# AREA
# ============================================================

area_number = 1
round_number = 1

area_names = {
    1: "DEAD STREETS",
    2: "INDUSTRIAL YARD"
}

# ============================================================
# CADENCE AGENT
# ============================================================

player_x = WIDTH / 2
player_y = HEIGHT / 2 + 190

player_radius = 22
player_speed = 390

player_health = 100
max_player_health = 100

# Damage protection
player_invulnerable = False
player_invulnerable_timer = 0
player_invulnerable_duration = 0.75

player_hit_flash = 0

game_over = False

# ============================================================
# WEAPONS
# ============================================================

current_weapon = "RIFLE"
special_ammo = 0

bullets = []
flames = []

bullet_speed = 1275

fire_timer = 0

muzzle_flash_timer = 0
muzzle_flash_duration = 0.05

# ============================================================
# CREATE BOSS
# ============================================================

def create_boss():

    boss_health = 1800

    zombies.append({
        "x": float(WIDTH / 2),
        "y": float(ARENA_TOP + 128),

        "radius": 46,
        "type": "BOSS",

        "speed": 87,
        "damage": 35,
        "score_value": 2500,

        "health": boss_health,
        "max_health": boss_health,

        "hit_flash": 0,

        # Charge attack
        "charge_timer": 2.5,
        "charge_duration": 0,
        "charge_dx": 0,
        "charge_dy": 0,
        "charge_speed": 585,
        "avoid_direction": random.choice([-1, 1])
    })

# ============================================================
# DROPS
# ============================================================

drops = []
pickup_radius = 42

# ============================================================
# ZOMBIES / ROUND
# ============================================================

zombies = []

score = 0
total_kills = 0
round_kills = 0

zombies_to_spawn = 15
zombies_spawned = 0

spawn_timer = 0
spawn_delay = 1.0

round_complete = False

# Boss state
boss_spawned = False
boss_defeated = False
boss_intro_timer = 0
boss_intro_duration = 2.0

# ============================================================
# OFFICIAL CADENCE BRAIN
# ============================================================

# These are the actions chosen by the real Cadence Brain.
CADENCE_ACTIONS = [
    "KITE",
    "STRAFE_LEFT",
    "STRAFE_RIGHT",
    "CHASE",
    "HOLD",
    "SEEK_HEALTH",
    "SEEK_WEAPON"
]

CADENCE_INPUTS = 5
CADENCE_VERSION = "0.74.0"

cadence_brain = None
cadence_action = "KITE"
cadence_reward_buffer = 0.0
cadence_decision_timer = 0.0
cadence_decision_interval = 0.30

cadence_decisions = 0
cadence_kills = 0
cadence_hits = 0
cadence_pickups = 0
cadence_deaths = 0
cadence_last_reward = 0.0

cadence_goal_text = "SCANNING"
cadence_target = None
game_over_timer = 0.0
cadence_terminal_sent = False
cadence_has_pending_action = False

# Navigation safety state.
cadence_emergency_timer = 0.0
cadence_stuck_timer = 0.0
cadence_unstuck_timer = 0.0
cadence_path = []
cadence_path_goal = None
cadence_path_replan_timer = 0.0

# Persistent emergency/recovery destination.
cadence_escape_waypoint = None
cadence_escape_replan_timer = 0.0

CADENCE_NAV_CELL = 46
CADENCE_REPATH_TIME = 0.45

CADENCE_CHECKPOINT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "cadence_deadzone_official_brain_v2.npz"
)

CADENCE_CHECKPOINT_BACKUP = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "cadence_deadzone_official_brain_v2_backup.npz"
)

CADENCE_STATS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "cadence_training_stats.json"
)

training_stats = {
    "total_runs": 0,
    "total_deaths": 0,
    "total_kills": 0,
    "total_area_clears": 0,
    "total_survival_seconds": 0.0,
    "best_survival_seconds": 0.0,
    "best_area": 1,
    "best_score": 0
}

run_elapsed = 0.0
run_recorded = False
startup_overlay_timer = 3.0

# ============================================================
# EXIT
# ============================================================

exit_active = False

exit_x = WIDTH / 2
exit_y = ARENA_TOP + 68

exit_radius = 45

# ============================================================
# TRANSITION
# ============================================================

transition_active = False
transition_timer = 0
transition_duration = 2.2

# ============================================================
# UTILITY
# ============================================================

def distance(x1, y1, x2, y2):

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )


# ============================================================
# MAP OBJECTS / COLLISION
# ============================================================

def get_crate_positions():
    """Crates drawn in Area 2+ and used as solid collision objects."""
    return [
        (150, 145), (195, 145),
        (1030, 155), (1075, 155),
        (160, 520),
        (1050, 500),
        (1520, 170),
        (1580, 760),
    ]


def get_map_obstacles():
    """Return every solid object in the current arena."""
    obstacles = []

    if area_number == 1:
        # Central fountain / monument.
        obstacles.append({
            "shape": "circle",
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "radius": 72
        })

    else:
        # Industrial crates are solid.
        for crate_x, crate_y in get_crate_positions():
            obstacles.append({
                "shape": "rect",
                "rect": pygame.Rect(
                    crate_x,
                    crate_y,
                    38,
                    38
                )
            })

    return obstacles


def circle_hits_rect(x, y, radius, rect):
    closest_x = max(
        rect.left,
        min(x, rect.right)
    )

    closest_y = max(
        rect.top,
        min(y, rect.bottom)
    )

    dx = x - closest_x
    dy = y - closest_y

    return (
        dx * dx +
        dy * dy
    ) < radius * radius


def circle_hits_map(x, y, radius):
    # Arena walls are also solid.
    if (
        x - radius < ARENA_LEFT
        or
        x + radius > ARENA_RIGHT
        or
        y - radius < ARENA_TOP
        or
        y + radius > ARENA_BOTTOM
    ):
        return True

    for obstacle in get_map_obstacles():

        if obstacle["shape"] == "circle":

            if distance(
                x,
                y,
                obstacle["x"],
                obstacle["y"]
            ) < (
                radius +
                obstacle["radius"]
            ):
                return True

        elif obstacle["shape"] == "rect":

            if circle_hits_rect(
                x,
                y,
                radius,
                obstacle["rect"]
            ):
                return True

    return False


def move_circle_with_map_collision(
    x,
    y,
    move_x,
    move_y,
    radius
):
    """Move one axis at a time so actors slide along walls/objects."""

    new_x = x + move_x

    if not circle_hits_map(
        new_x,
        y,
        radius
    ):
        x = new_x

    new_y = y + move_y

    if not circle_hits_map(
        x,
        new_y,
        radius
    ):
        y = new_y

    return x, y


def move_zombie_toward_player(
    zombie,
    speed,
    dt
):
    """Chase the player while sliding around fountains and crates."""

    old_x = zombie["x"]
    old_y = zombie["y"]

    angle = math.atan2(
        player_y - old_y,
        player_x - old_x
    )

    step = speed * dt

    move_x = math.cos(angle) * step
    move_y = math.sin(angle) * step

    new_x, new_y = move_circle_with_map_collision(
        old_x,
        old_y,
        move_x,
        move_y,
        zombie["radius"]
    )

    moved = distance(
        old_x,
        old_y,
        new_x,
        new_y
    )

    # If the direct route is blocked, move sideways around the object.
    if moved < step * 0.30:

        avoid_direction = zombie.get(
            "avoid_direction",
            1
        )

        side_angle = (
            angle +
            avoid_direction *
            math.pi / 2
        )

        side_x = math.cos(
            side_angle
        ) * step

        side_y = math.sin(
            side_angle
        ) * step

        alt_x, alt_y = move_circle_with_map_collision(
            old_x,
            old_y,
            side_x,
            side_y,
            zombie["radius"]
        )

        alt_moved = distance(
            old_x,
            old_y,
            alt_x,
            alt_y
        )

        if alt_moved > moved:
            new_x = alt_x
            new_y = alt_y

        else:
            # Try the other side next time.
            zombie["avoid_direction"] = (
                -avoid_direction
            )

    zombie["x"] = new_x
    zombie["y"] = new_y


def get_player_spawn():
    # Area 1 has a fountain at the center,
    # so spawn the player below it.
    if area_number == 1:
        return (
            WIDTH / 2,
            HEIGHT / 2 + 190
        )

    return (
        WIDTH / 2,
        HEIGHT / 2
    )

# ============================================================
# TRAINING TELEMETRY / COMPETITION STATS
# ============================================================

def cadence_load_training_stats():

    global training_stats

    try:
        if not os.path.exists(CADENCE_STATS_FILE):
            return

        with open(
            CADENCE_STATS_FILE,
            "r",
            encoding="utf-8"
        ) as stats_file:
            loaded = json.load(stats_file)

        for key in training_stats:
            if key in loaded:
                training_stats[key] = loaded[key]

    except Exception as error:
        print("Cadence stats load failed:", error)


def cadence_save_training_stats():

    try:
        temp_path = CADENCE_STATS_FILE + ".tmp"

        with open(
            temp_path,
            "w",
            encoding="utf-8"
        ) as stats_file:
            json.dump(
                training_stats,
                stats_file,
                indent=2
            )

        os.replace(
            temp_path,
            CADENCE_STATS_FILE
        )

    except Exception as error:
        print("Cadence stats save failed:", error)


def cadence_record_area_clear():

    training_stats["total_area_clears"] += 1
    training_stats["best_area"] = max(
        int(training_stats["best_area"]),
        int(area_number)
    )

    cadence_save_training_stats()


def cadence_record_run():

    global run_recorded

    if run_recorded:
        return

    run_recorded = True

    training_stats["total_runs"] += 1
    training_stats["total_deaths"] += 1
    training_stats["total_kills"] += int(total_kills)
    training_stats["total_survival_seconds"] += float(run_elapsed)
    training_stats["best_survival_seconds"] = max(
        float(training_stats["best_survival_seconds"]),
        float(run_elapsed)
    )
    training_stats["best_area"] = max(
        int(training_stats["best_area"]),
        int(area_number)
    )
    training_stats["best_score"] = max(
        int(training_stats["best_score"]),
        int(score)
    )

    cadence_save_training_stats()


def cadence_average_survival():

    runs = max(
        1,
        int(training_stats["total_runs"])
    )

    return (
        float(training_stats["total_survival_seconds"])
        / runs
    )


def cadence_active_boss():

    for zombie in zombies:
        if zombie.get("type") == "BOSS":
            return zombie

    return None


def cadence_corner_pressure():

    margin = 165

    near_left = (
        player_x < ARENA_LEFT + margin
    )
    near_right = (
        player_x > ARENA_RIGHT - margin
    )
    near_top = (
        player_y < ARENA_TOP + margin
    )
    near_bottom = (
        player_y > ARENA_BOTTOM - margin
    )

    in_corner = (
        (near_left or near_right)
        and
        (near_top or near_bottom)
    )

    if not in_corner:
        return False

    return any(
        distance(
            player_x,
            player_y,
            zombie["x"],
            zombie["y"]
        ) < 360
        for zombie in zombies
    )


def cadence_boss_safety_move(
    boss,
    dt
):

    if boss is None:
        return False

    boss_distance = distance(
        player_x,
        player_y,
        boss["x"],
        boss["y"]
    )

    # During a charge, dodge perpendicular to the charge vector.
    if boss.get("charge_duration", 0) > 0:

        charge_dx = boss.get("charge_dx", 0.0)
        charge_dy = boss.get("charge_dy", 0.0)

        side_a = (
            -charge_dy,
            charge_dx
        )

        side_b = (
            charge_dy,
            -charge_dx
        )

        candidates = []

        for side_dx, side_dy in (
            side_a,
            side_b
        ):

            goal_x = (
                player_x +
                side_dx * 360
            )

            goal_y = (
                player_y +
                side_dy * 360
            )

            goal_x = max(
                ARENA_LEFT + 50,
                min(
                    ARENA_RIGHT - 50,
                    goal_x
                )
            )

            goal_y = max(
                ARENA_TOP + 50,
                min(
                    ARENA_BOTTOM - 50,
                    goal_y
                )
            )

            score = cadence_enemy_safety_score(
                goal_x,
                goal_y
            )

            if not circle_hits_map(
                goal_x,
                goal_y,
                player_radius + 8
            ):
                candidates.append(
                    (
                        score,
                        goal_x,
                        goal_y
                    )
                )

        if candidates:

            candidates.sort(
                key=lambda item: item[0],
                reverse=True
            )

            _, goal_x, goal_y = candidates[0]

            cadence_safe_move_toward(
                goal_x,
                goal_y,
                dt,
                1.34
            )

            return True

    # Do not let the Brute pin Cadence at point-blank range.
    if boss_distance < 245:
        cadence_escape_move(dt)
        return True

    return False


# ============================================================
# OFFICIAL CADENCE SDK INTEGRATION
# ============================================================

def create_official_cadence_brain():

    print("CADENCE: creating official brain...")

    brain = Brain.compose(
        inputs=CADENCE_INPUTS,
        actions=len(CADENCE_ACTIONS),
        modules=(16, 8),
        seed=42
    )

    print("CADENCE: official brain ready.")

    return brain


def cadence_load_official_brain():

    global cadence_brain
    global cadence_has_pending_action

    candidates = [
        CADENCE_CHECKPOINT,
        CADENCE_CHECKPOINT_BACKUP
    ]

    for checkpoint_path in candidates:

        if not os.path.exists(
            checkpoint_path
        ):
            continue

        try:

            cadence_brain = (
                Brain.load(
                    checkpoint_path
                )
            )

            cadence_has_pending_action = True

            print(
                "Loaded official Cadence checkpoint:",
                checkpoint_path
            )

            return

        except Exception as error:

            print(
                "Cadence checkpoint load failed:",
                checkpoint_path,
                error
            )

    cadence_brain = (
        create_official_cadence_brain()
    )

    cadence_has_pending_action = False


def cadence_save_official_brain():

    if cadence_brain is None:
        return

    try:

        # Keep the last known-good checkpoint as a fallback.
        if os.path.exists(
            CADENCE_CHECKPOINT
        ):
            try:
                shutil.copy2(
                    CADENCE_CHECKPOINT,
                    CADENCE_CHECKPOINT_BACKUP
                )
            except Exception:
                pass

        cadence_brain.save(
            CADENCE_CHECKPOINT
        )

    except Exception as error:

        print(
            "Cadence checkpoint save failed:",
            error
        )


def cadence_nearest_enemy():

    if not zombies:
        return None, 99999.0

    bosses = [
        zombie
        for zombie in zombies
        if zombie.get(
            "type"
        ) == "BOSS"
    ]

    pool = (
        bosses
        if bosses
        else zombies
    )

    target = min(
        pool,
        key=lambda zombie: distance(
            player_x,
            player_y,
            zombie["x"],
            zombie["y"]
        )
    )

    return (
        target,
        distance(
            player_x,
            player_y,
            target["x"],
            target["y"]
        )
    )


def cadence_nearest_drop(
    drop_types
):

    candidates = [
        drop
        for drop in drops
        if drop["type"] in drop_types
    ]

    if not candidates:
        return None

    return min(
        candidates,
        key=lambda drop: distance(
            player_x,
            player_y,
            drop["x"],
            drop["y"]
        )
    )


def cadence_observation():

    target, target_distance = (
        cadence_nearest_enemy()
    )

    health_input = (
        player_health /
        max_player_health
    )

    enemy_input = (
        0.0
        if target is None
        else 1.0 -
        min(
            1.0,
            target_distance / 900.0
        )
    )

    horde_input = min(
        1.0,
        len(zombies) / 14.0
    )

    medkit = cadence_nearest_drop(
        {"MEDKIT"}
    )

    if medkit is None:

        medkit_input = 0.0

    else:

        medkit_distance = distance(
            player_x,
            player_y,
            medkit["x"],
            medkit["y"]
        )

        medkit_input = (
            1.0 -
            min(
                1.0,
                medkit_distance / 1200.0
            )
        )

    weapon = cadence_nearest_drop(
        {
            "MACHINE GUN",
            "FLAMETHROWER"
        }
    )

    if weapon is None:

        weapon_input = 0.0

    else:

        weapon_distance = distance(
            player_x,
            player_y,
            weapon["x"],
            weapon["y"]
        )

        weapon_input = (
            1.0 -
            min(
                1.0,
                weapon_distance / 1200.0
            )
        )

    return np.asarray(
        [
            health_input,
            enemy_input,
            horde_input,
            medkit_input,
            weapon_input
        ],
        dtype=np.float64
    )


def cadence_choose_official_action(
    reward=0.0,
    done=False
):

    global cadence_action
    global cadence_decisions
    global cadence_last_reward
    global cadence_has_pending_action

    if cadence_brain is None:
        return cadence_action

    observation = (
        cadence_observation()
    )

    reward_array = np.asarray(
        [
            float(reward)
        ],
        dtype=np.float64
    )

    done_array = np.asarray(
        [
            bool(done)
        ],
        dtype=bool
    )

    try:

        observation_batch = (
            observation.reshape(
                1,
                CADENCE_INPUTS
            )
        )

        if cadence_has_pending_action:

            result = cadence_brain.step(
                observation_batch,
                reward=reward_array,
                done=done_array
            )

        else:

            # The first observation in a life has no previous
            # action to reward.
            result = cadence_brain.step(
                observation_batch
            )

        action_index = int(
            np.asarray(
                result
            ).reshape(
                -1
            )[0]
        )

        action_index = max(
            0,
            min(
                len(CADENCE_ACTIONS) - 1,
                action_index
            )
        )

        cadence_action = (
            CADENCE_ACTIONS[
                action_index
            ]
        )

        cadence_last_reward = (
            float(reward)
        )

        cadence_decisions += 1

        cadence_has_pending_action = (
            not bool(done)
        )

        if (
            cadence_decisions %
            20
            == 0
        ):
            cadence_save_official_brain()

        return cadence_action

    except Exception as error:

        print(
            "Cadence step refused/failed:",
            error
        )

        # Keep the last valid Cadence action.
        return cadence_action


def cadence_terminal_feedback():

    global cadence_terminal_sent
    global cadence_reward_buffer

    if cadence_terminal_sent:
        return

    cadence_terminal_sent = True

    cadence_choose_official_action(
        reward=cadence_reward_buffer,
        done=True
    )

    cadence_reward_buffer = 0.0

    cadence_save_official_brain()


def cadence_reset_navigation():

    global cadence_path
    global cadence_path_goal
    global cadence_path_replan_timer

    cadence_path = []
    cadence_path_goal = None
    cadence_path_replan_timer = 0.0


def cadence_line_clear(
    x1,
    y1,
    x2,
    y2,
    radius=None
):

    if radius is None:
        radius = player_radius + 4

    total_distance = distance(
        x1,
        y1,
        x2,
        y2
    )

    if total_distance <= 1:
        return True

    samples = max(
        1,
        int(
            total_distance / 24
        )
    )

    for index in range(
        1,
        samples + 1
    ):

        amount = (
            index /
            samples
        )

        sample_x = (
            x1 +
            (x2 - x1) *
            amount
        )

        sample_y = (
            y1 +
            (y2 - y1) *
            amount
        )

        if circle_hits_map(
            sample_x,
            sample_y,
            radius
        ):
            return False

    return True


def cadence_world_to_cell(
    x,
    y
):

    col = int(
        (
            x -
            ARENA_LEFT
        ) /
        CADENCE_NAV_CELL
    )

    row = int(
        (
            y -
            ARENA_TOP
        ) /
        CADENCE_NAV_CELL
    )

    return (
        col,
        row
    )


def cadence_cell_center(
    cell
):

    col, row = cell

    x = (
        ARENA_LEFT +
        col *
        CADENCE_NAV_CELL +
        CADENCE_NAV_CELL / 2
    )

    y = (
        ARENA_TOP +
        row *
        CADENCE_NAV_CELL +
        CADENCE_NAV_CELL / 2
    )

    return (
        x,
        y
    )


def cadence_grid_size():

    cols = max(
        1,
        int(
            (
                ARENA_RIGHT -
                ARENA_LEFT
            ) /
            CADENCE_NAV_CELL
        )
    )

    rows = max(
        1,
        int(
            (
                ARENA_BOTTOM -
                ARENA_TOP
            ) /
            CADENCE_NAV_CELL
        )
    )

    return (
        cols,
        rows
    )


def cadence_cell_walkable(
    cell
):

    col, row = cell
    cols, rows = (
        cadence_grid_size()
    )

    if (
        col < 0
        or
        row < 0
        or
        col >= cols
        or
        row >= rows
    ):
        return False

    x, y = cadence_cell_center(
        cell
    )

    return not circle_hits_map(
        x,
        y,
        player_radius + 11
    )


def cadence_nearest_walkable_cell(
    starting_cell
):

    if cadence_cell_walkable(
        starting_cell
    ):
        return starting_cell

    for radius in range(
        1,
        7
    ):

        for dx in range(
            -radius,
            radius + 1
        ):

            for dy in range(
                -radius,
                radius + 1
            ):

                if (
                    abs(dx) != radius
                    and
                    abs(dy) != radius
                ):
                    continue

                candidate = (
                    starting_cell[0] + dx,
                    starting_cell[1] + dy
                )

                if cadence_cell_walkable(
                    candidate
                ):
                    return candidate

    return None


def cadence_plan_path(
    goal_x,
    goal_y
):

    start_cell = (
        cadence_nearest_walkable_cell(
            cadence_world_to_cell(
                player_x,
                player_y
            )
        )
    )

    goal_cell = (
        cadence_nearest_walkable_cell(
            cadence_world_to_cell(
                goal_x,
                goal_y
            )
        )
    )

    if (
        start_cell is None
        or
        goal_cell is None
    ):
        return []

    if start_cell == goal_cell:
        return [
            (
                goal_x,
                goal_y
            )
        ]

    open_heap = []

    heapq.heappush(
        open_heap,
        (
            0.0,
            start_cell
        )
    )

    came_from = {}
    g_score = {
        start_cell: 0.0
    }

    closed = set()

    directions = [
        (-1, 0, 1.0),
        (1, 0, 1.0),
        (0, -1, 1.0),
        (0, 1, 1.0),
        (-1, -1, 1.414),
        (-1, 1, 1.414),
        (1, -1, 1.414),
        (1, 1, 1.414),
    ]

    while open_heap:

        _, current = heapq.heappop(
            open_heap
        )

        if current in closed:
            continue

        if current == goal_cell:
            break

        closed.add(
            current
        )

        for dx, dy, move_cost in directions:

            neighbor = (
                current[0] + dx,
                current[1] + dy
            )

            if not cadence_cell_walkable(
                neighbor
            ):
                continue

            # No diagonal corner-cutting through obstacles.
            if (
                dx != 0
                and
                dy != 0
            ):

                side_a = (
                    current[0] + dx,
                    current[1]
                )

                side_b = (
                    current[0],
                    current[1] + dy
                )

                if (
                    not cadence_cell_walkable(
                        side_a
                    )
                    or
                    not cadence_cell_walkable(
                        side_b
                    )
                ):
                    continue

            tentative = (
                g_score[current] +
                move_cost
            )

            if tentative >= g_score.get(
                neighbor,
                999999.0
            ):
                continue

            came_from[neighbor] = (
                current
            )

            g_score[neighbor] = (
                tentative
            )

            heuristic = math.hypot(
                goal_cell[0] -
                neighbor[0],
                goal_cell[1] -
                neighbor[1]
            )

            heapq.heappush(
                open_heap,
                (
                    tentative +
                    heuristic,
                    neighbor
                )
            )

    if goal_cell not in came_from:
        return []

    cells = [
        goal_cell
    ]

    current = goal_cell

    while current != start_cell:

        current = came_from[
            current
        ]

        cells.append(
            current
        )

    cells.reverse()

    path = [
        cadence_cell_center(
            cell
        )
        for cell in cells[1:]
    ]

    if not circle_hits_map(
        goal_x,
        goal_y,
        player_radius
    ):
        path.append(
            (
                goal_x,
                goal_y
            )
        )

    return path


def cadence_enemy_safety_score(
    x,
    y
):

    if not zombies:
        return 1000.0

    distances = sorted(
        distance(
            x,
            y,
            zombie["x"],
            zombie["y"]
        )
        for zombie in zombies
    )

    nearest = distances[:4]

    score = 0.0

    weights = [
        1.0,
        0.55,
        0.30,
        0.18
    ]

    for index, enemy_distance in enumerate(
        nearest
    ):

        score += (
            enemy_distance *
            weights[index]
        )

    return score


def cadence_find_safe_point(
    prefer_x=None,
    prefer_y=None
):
    """
    Pick a reachable open point with maximum zombie clearance.
    Used for emergency movement and unsticking.
    """

    best = None
    best_score = -999999.0

    rings = (
        150,
        220,
        300,
        380
    )

    for radius in rings:

        for index in range(32):

            angle = (
                math.tau *
                index /
                32
            )

            test_x = (
                player_x +
                math.cos(angle) *
                radius
            )

            test_y = (
                player_y +
                math.sin(angle) *
                radius
            )

            # Keep the destination inside the arena.
            if (
                test_x < ARENA_LEFT + player_radius + 14
                or
                test_x > ARENA_RIGHT - player_radius - 14
                or
                test_y < ARENA_TOP + player_radius + 14
                or
                test_y > ARENA_BOTTOM - player_radius - 14
            ):
                continue

            if circle_hits_map(
                test_x,
                test_y,
                player_radius + 8
            ):
                continue

            # Candidate must be reachable either directly or by A*.
            direct = cadence_line_clear(
                player_x,
                player_y,
                test_x,
                test_y
            )

            if direct:
                route_cost = distance(
                    player_x,
                    player_y,
                    test_x,
                    test_y
                )
            else:
                planned = cadence_plan_path(
                    test_x,
                    test_y
                )

                if not planned:
                    continue

                route_cost = (
                    len(planned) *
                    CADENCE_NAV_CELL
                )

            score = (
                cadence_enemy_safety_score(
                    test_x,
                    test_y
                ) *
                3.2
            )

            # Prefer open central space over being trapped on an edge.
            edge_clearance = min(
                test_x - ARENA_LEFT,
                ARENA_RIGHT - test_x,
                test_y - ARENA_TOP,
                ARENA_BOTTOM - test_y
            )

            score += (
                edge_clearance *
                0.34
            )

            # Shorter escape paths are better.
            score -= (
                route_cost *
                0.11
            )

            # When seeking a medkit, still bias movement toward it.
            if (
                prefer_x is not None
                and
                prefer_y is not None
            ):
                score -= (
                    distance(
                        test_x,
                        test_y,
                        prefer_x,
                        prefer_y
                    ) *
                    0.18
                )

            if score > best_score:

                best_score = score
                best = (
                    test_x,
                    test_y
                )

    # Last-resort fallback: arena center if it is legal.
    if best is None:

        center_x = (
            ARENA_LEFT +
            ARENA_RIGHT
        ) / 2

        center_y = (
            ARENA_TOP +
            ARENA_BOTTOM
        ) / 2

        if not circle_hits_map(
            center_x,
            center_y,
            player_radius + 8
        ):
            best = (
                center_x,
                center_y
            )

    return best


def cadence_escape_move(
    dt,
    prefer_x=None,
    prefer_y=None
):

    global cadence_escape_waypoint
    global cadence_escape_replan_timer

    cadence_escape_replan_timer -= dt

    need_new_point = (
        cadence_escape_waypoint is None
        or
        cadence_escape_replan_timer <= 0
        or
        distance(
            player_x,
            player_y,
            cadence_escape_waypoint[0],
            cadence_escape_waypoint[1]
        ) < 42
    )

    if need_new_point:

        cadence_escape_waypoint = (
            cadence_find_safe_point(
                prefer_x,
                prefer_y
            )
        )

        cadence_escape_replan_timer = 0.42

    if cadence_escape_waypoint is None:
        return

    cadence_safe_move_toward(
        cadence_escape_waypoint[0],
        cadence_escape_waypoint[1],
        dt,
        1.34,
        allow_recovery=False
    )


def cadence_safe_move_toward(
    goal_x,
    goal_y,
    dt,
    speed_scale=1.0,
    allow_recovery=True
):

    global player_x
    global player_y
    global cadence_path
    global cadence_path_goal
    global cadence_path_replan_timer
    global cadence_stuck_timer
    global cadence_unstuck_timer
    global cadence_escape_waypoint
    global cadence_escape_replan_timer

    # Clamp targets to a legal point inside the arena.
    goal_x = max(
        ARENA_LEFT + player_radius + 12,
        min(
            ARENA_RIGHT - player_radius - 12,
            goal_x
        )
    )

    goal_y = max(
        ARENA_TOP + player_radius + 12,
        min(
            ARENA_BOTTOM - player_radius - 12,
            goal_y
        )
    )

    dx = (
        goal_x -
        player_x
    )

    dy = (
        goal_y -
        player_y
    )

    goal_distance = math.hypot(
        dx,
        dy
    )

    if goal_distance < 5:
        cadence_stuck_timer = 0.0
        return

    cadence_path_replan_timer -= dt

    goal_changed = (
        cadence_path_goal is None
        or
        distance(
            cadence_path_goal[0],
            cadence_path_goal[1],
            goal_x,
            goal_y
        ) > 70
    )

    if cadence_line_clear(
        player_x,
        player_y,
        goal_x,
        goal_y
    ):

        waypoint_x = goal_x
        waypoint_y = goal_y

        cadence_path = []
        cadence_path_goal = (
            goal_x,
            goal_y
        )

    else:

        if (
            not cadence_path
            or
            goal_changed
            or
            cadence_path_replan_timer <= 0
        ):

            cadence_path = (
                cadence_plan_path(
                    goal_x,
                    goal_y
                )
            )

            cadence_path_goal = (
                goal_x,
                goal_y
            )

            cadence_path_replan_timer = 0.22

        while (
            cadence_path
            and
            distance(
                player_x,
                player_y,
                cadence_path[0][0],
                cadence_path[0][1]
            ) < 30
        ):
            cadence_path.pop(0)

        if cadence_path:

            waypoint_x = (
                cadence_path[0][0]
            )

            waypoint_y = (
                cadence_path[0][1]
            )

        else:

            # No route to that exact destination.
            # Do not stand still: immediately pick an open recovery point.
            if allow_recovery:
                cadence_unstuck_timer = 0.85
                cadence_escape_waypoint = None
                cadence_escape_replan_timer = 0.0
            return

    move_dx = (
        waypoint_x -
        player_x
    )

    move_dy = (
        waypoint_y -
        player_y
    )

    move_length = math.hypot(
        move_dx,
        move_dy
    )

    if move_length <= 0:
        return

    move_dx /= move_length
    move_dy /= move_length

    step = (
        player_speed *
        speed_scale *
        dt
    )

    old_x = player_x
    old_y = player_y

    player_x, player_y = (
        move_circle_with_map_collision(
            player_x,
            player_y,
            move_dx * step,
            move_dy * step,
            player_radius
        )
    )

    actual_move = distance(
        old_x,
        old_y,
        player_x,
        player_y
    )

    # Faster stuck detection.
    if (
        goal_distance > 55
        and
        actual_move < step * 0.24
    ):
        cadence_stuck_timer += dt
    else:
        cadence_stuck_timer = max(
            0.0,
            cadence_stuck_timer -
            dt * 3.2
        )

    if (
        allow_recovery
        and
        cadence_stuck_timer > 0.22
    ):

        cadence_stuck_timer = 0.0
        cadence_unstuck_timer = 0.95

        cadence_path = []
        cadence_path_goal = None
        cadence_path_replan_timer = 0.0

        cadence_escape_waypoint = None
        cadence_escape_replan_timer = 0.0


def cadence_combat_move(
    action,
    target,
    target_distance,
    dt
):

    if target is None:

        cadence_safe_move_toward(
            WIDTH / 2,
            HEIGHT / 2,
            dt,
            0.75
        )

        return

    tx = target["x"]
    ty = target["y"]

    angle = math.atan2(
        ty - player_y,
        tx - player_x
    )

    desired_range = 300

    if current_weapon == "FLAMETHROWER":
        desired_range = 200

    elif current_weapon == "MACHINE GUN":
        desired_range = 350

    # Never stand still when an enemy is already on top of Cadence.
    if target_distance < 145:

        cadence_escape_move(
            dt
        )

        return

    if action == "CHASE":

        if target_distance > desired_range:

            cadence_safe_move_toward(
                tx,
                ty,
                dt,
                1.00
            )

        else:

            side_angle = (
                angle +
                math.pi / 2
            )

            cadence_safe_move_toward(
                player_x +
                math.cos(side_angle) * 230,
                player_y +
                math.sin(side_angle) * 230,
                dt,
                1.05
            )

    elif action == "KITE":

        if target_distance < (
            desired_range - 45
        ):

            cadence_safe_move_toward(
                player_x -
                math.cos(angle) * 320,
                player_y -
                math.sin(angle) * 320,
                dt,
                1.18
            )

        elif target_distance > (
            desired_range + 160
        ):

            cadence_safe_move_toward(
                tx,
                ty,
                dt,
                0.84
            )

        else:

            side_angle = (
                angle +
                math.pi / 2
            )

            cadence_safe_move_toward(
                player_x +
                math.cos(side_angle) * 185,
                player_y +
                math.sin(side_angle) * 185,
                dt,
                0.88
            )

    elif action in (
        "STRAFE_LEFT",
        "STRAFE_RIGHT"
    ):

        side = (
            -1
            if action == "STRAFE_LEFT"
            else 1
        )

        side_angle = (
            angle +
            side *
            math.pi / 2
        )

        goal_x = (
            player_x +
            math.cos(side_angle) * 270
        )

        goal_y = (
            player_y +
            math.sin(side_angle) * 270
        )

        if target_distance < (
            desired_range * 0.78
        ):

            goal_x -= (
                math.cos(angle) * 220
            )

            goal_y -= (
                math.sin(angle) * 220
            )

        cadence_safe_move_toward(
            goal_x,
            goal_y,
            dt,
            1.08
        )

    elif action == "HOLD":

        # HOLD means hold distance while circling, never freeze.
        side = (
            1
            if (
                cadence_decisions //
                5
            ) % 2 == 0
            else -1
        )

        side_angle = (
            angle +
            side *
            math.pi / 2
        )

        goal_x = (
            player_x +
            math.cos(side_angle) * 190
        )

        goal_y = (
            player_y +
            math.sin(side_angle) * 190
        )

        if target_distance < (
            desired_range - 30
        ):

            goal_x -= (
                math.cos(angle) * 180
            )

            goal_y -= (
                math.sin(angle) * 180
            )

        cadence_safe_move_toward(
            goal_x,
            goal_y,
            dt,
            0.92
        )


def cadence_choose_priority_goal():

    medkit = cadence_nearest_drop(
        {
            "MEDKIT"
        }
    )

    # Survival rule:
    # Cadence must heal before it becomes critical.
    # High-level tactics are still learned by the Cadence brain,
    # but basic self-preservation is deterministic.
    if (
        player_health <= 72
        and
        medkit is not None
    ):

        return (
            "HEALTH PRIORITY",
            medkit
        )

    # If badly hurt, even a distant medkit is the most important objective.
    if (
        player_health <= 45
        and
        medkit is not None
    ):

        return (
            "CRITICAL HEALTH",
            medkit
        )

    # After the room is clear, heal before leaving if useful.
    if (
        exit_active
        and
        player_health < 88
        and
        medkit is not None
    ):

        return (
            "HEAL BEFORE EXIT",
            medkit
        )

    if exit_active:

        return (
            "EXIT",
            {
                "x": exit_x,
                "y": exit_y
            }
        )

    # Weapon pickup safety rule:
    # If Cadence only has the rifle, take a nearby special weapon
    # unless health is already dangerously low.
    if (
        current_weapon == "RIFLE"
        and
        player_health > 45
    ):

        weapon = cadence_nearest_drop(
            {
                "MACHINE GUN",
                "FLAMETHROWER"
            }
        )

        if (
            weapon is not None
            and
            distance(
                player_x,
                player_y,
                weapon["x"],
                weapon["y"]
            ) <= 520
        ):

            return (
                "WEAPON PICKUP",
                weapon
            )

    return (
        None,
        None
    )


def cadence_auto_fire(target):
    global fire_timer
    global special_ammo

    if target is None or fire_timer > 0:
        return

    aim = (target['x'], target['y'])
    target_distance = distance(player_x, player_y, target['x'], target['y'])

    if current_weapon == 'RIFLE':
        shoot_bullet(aim, 'RIFLE')
        fire_timer = 0.12

    elif current_weapon == 'MACHINE GUN' and special_ammo > 0:
        shoot_bullet(aim, 'MACHINE GUN')
        special_ammo -= 1
        fire_timer = 0.045

    elif current_weapon == 'FLAMETHROWER' and special_ammo > 0:
        # Don't waste flame fuel from across the arena.
        if target_distance <= 430:
            for _ in range(3):
                fire_flame(aim)
            special_ammo -= 1
            fire_timer = 0.035


def update_cadence_ai(
    dt
):

    global cadence_action
    global cadence_decision_timer
    global cadence_reward_buffer
    global cadence_goal_text
    global cadence_target
    global cadence_emergency_timer
    global cadence_unstuck_timer

    if (
        transition_active
        or
        game_over
    ):
        return

    if cadence_emergency_timer > 0:
        cadence_emergency_timer -= dt

    target, target_distance = (
        cadence_nearest_enemy()
    )

    cadence_target = target

    nearby_danger = sum(
        1
        for zombie in zombies
        if distance(
            player_x,
            player_y,
            zombie["x"],
            zombie["y"]
        ) < 205
    )

    forced_goal_type, forced_goal = (
        cadence_choose_priority_goal()
    )

    # --------------------------------------------------------
    # BOSS SAFETY / CORNER PREVENTION
    # --------------------------------------------------------

    boss = cadence_active_boss()

    if boss is not None:

        if cadence_boss_safety_move(
            boss,
            dt
        ):

            cadence_goal_text = "BOSS DODGE"

            cadence_auto_fire(
                boss
            )

            return

    if cadence_corner_pressure():

        cadence_goal_text = "ESCAPE CORNER"

        center_x = (
            ARENA_LEFT +
            ARENA_RIGHT
        ) / 2

        center_y = (
            ARENA_TOP +
            ARENA_BOTTOM
        ) / 2

        cadence_safe_move_toward(
            center_x,
            center_y,
            dt,
            1.28
        )

        cadence_auto_fire(
            target
        )

        return

    # --------------------------------------------------------
    # HARD SAFETY REFLEX
    # --------------------------------------------------------
    # This is navigation safety, not the learning policy.
    if (
        cadence_emergency_timer > 0
        or
        target_distance < 118
        or
        nearby_danger >= 2
    ):

        cadence_goal_text = "EVADE"

        prefer_x = None
        prefer_y = None

        if (
            forced_goal_type
            in (
                "HEALTH PRIORITY",
                "CRITICAL HEALTH",
                "HEAL BEFORE EXIT"
            )
            and
            forced_goal
            is not None
        ):

            prefer_x = (
                forced_goal["x"]
            )

            prefer_y = (
                forced_goal["y"]
            )

        cadence_escape_move(
            dt,
            prefer_x,
            prefer_y
        )

        cadence_auto_fire(
            target
        )

        return

    # --------------------------------------------------------
    # STUCK RECOVERY
    # --------------------------------------------------------
    if cadence_unstuck_timer > 0:

        cadence_goal_text = "UNSTUCK"

        prefer_x = None
        prefer_y = None

        if (
            forced_goal is not None
            and
            forced_goal_type
            in (
                "HEALTH PRIORITY",
                "CRITICAL HEALTH",
                "HEAL BEFORE EXIT",
                "WEAPON PICKUP",
                "EXIT"
            )
        ):
            prefer_x = forced_goal["x"]
            prefer_y = forced_goal["y"]

        cadence_escape_move(
            dt,
            prefer_x,
            prefer_y
        )

        cadence_unstuck_timer = max(
            0.0,
            cadence_unstuck_timer -
            dt
        )

        cadence_auto_fire(
            target
        )

        return

    # --------------------------------------------------------
    # EXIT / CRITICAL HEALTH SAFETY
    # --------------------------------------------------------
    if forced_goal is not None:

        cadence_goal_text = (
            forced_goal_type
        )

        forced_speed = 1.12

        if forced_goal_type in (
            "HEALTH PRIORITY",
            "CRITICAL HEALTH",
            "HEAL BEFORE EXIT"
        ):
            forced_speed = 1.28

        elif forced_goal_type == "WEAPON PICKUP":
            forced_speed = 1.16

        cadence_safe_move_toward(
            forced_goal["x"],
            forced_goal["y"],
            dt,
            forced_speed
        )

        cadence_auto_fire(
            target
        )

        return

    # --------------------------------------------------------
    # REAL CADENCE BRAIN DECISION
    # --------------------------------------------------------
    cadence_decision_timer -= dt

    if cadence_decision_timer <= 0:

        cadence_action = (
            cadence_choose_official_action(
                reward=cadence_reward_buffer,
                done=False
            )
        )

        cadence_reward_buffer = 0.0

        cadence_decision_timer = (
            cadence_decision_interval
        )

    # --------------------------------------------------------
    # ACTION ADAPTER
    # --------------------------------------------------------
    if cadence_action == "SEEK_HEALTH":

        medkit = cadence_nearest_drop(
            {
                "MEDKIT"
            }
        )

        if medkit is not None:

            cadence_goal_text = (
                "CADENCE: HEALTH"
            )

            cadence_safe_move_toward(
                medkit["x"],
                medkit["y"],
                dt,
                1.13
            )

        else:

            # Penalize impossible/no-op choices gently.
            cadence_reward_buffer -= 0.05

            cadence_goal_text = "COMBAT"

            cadence_combat_move(
                "KITE",
                target,
                target_distance,
                dt
            )

    elif cadence_action == "SEEK_WEAPON":

        weapon = cadence_nearest_drop(
            {
                "MACHINE GUN",
                "FLAMETHROWER"
            }
        )

        if weapon is not None:

            cadence_goal_text = (
                "CADENCE: WEAPON"
            )

            cadence_safe_move_toward(
                weapon["x"],
                weapon["y"],
                dt,
                1.10
            )

        else:

            cadence_reward_buffer -= 0.05

            cadence_goal_text = "COMBAT"

            cadence_combat_move(
                "STRAFE_LEFT",
                target,
                target_distance,
                dt
            )

    else:

        cadence_goal_text = (
            "CADENCE BRAIN"
        )

        cadence_combat_move(
            cadence_action,
            target,
            target_distance,
            dt
        )

    cadence_auto_fire(
        target
    )


def draw_cadence(surface):
    x = int(player_x)
    y = int(player_y)

    target = cadence_target
    if target is not None:
        angle = math.atan2(target['y'] - player_y, target['x'] - player_x)
    else:
        angle = -math.pi / 2

    dx = math.cos(angle)
    dy = math.sin(angle)

    # Strong blue AI glow.
    draw_soft_glow(surface, BLUE, x, y, 40, 48)

    pygame.draw.ellipse(
        surface,
        (5, 8, 11),
        (x - 25, y + 16, 50, 18)
    )

    # Armored AI body.
    pygame.draw.circle(surface, (62, 128, 178), (x, y), 22)
    pygame.draw.circle(surface, (19, 46, 70), (x, y), 22, 5)
    pygame.draw.rect(surface, (34, 73, 101), (x - 16, y - 4, 32, 24), border_radius=7)

    # AI core / visor.
    pygame.draw.circle(surface, WHITE, (x, y - 8), 9)
    pygame.draw.circle(surface, BLUE, (x, y - 8), 5)

    # Weapon follows the current target.
    gun_length = 46
    gun_width = 9
    gun_color = (48, 57, 66)

    if current_weapon == 'MACHINE GUN':
        gun_length = 56
        gun_width = 11
        gun_color = (52, 74, 94)
    elif current_weapon == 'FLAMETHROWER':
        gun_length = 58
        gun_width = 12
        gun_color = (105, 74, 40)

    gx = x + dx * gun_length
    gy = y + dy * gun_length

    pygame.draw.line(surface, gun_color, (x, y), (int(gx), int(gy)), gun_width)
    pygame.draw.line(surface, BLUE, (x, y), (int(gx), int(gy)), 2)

    if muzzle_flash_timer > 0:
        fx = x + dx * (gun_length + 8)
        fy = y + dy * (gun_length + 8)
        draw_soft_glow(surface, ORANGE, fx, fy, 18, 70)
        pygame.draw.circle(surface, YELLOW, (int(fx), int(fy)), 7)

    label = font_small.render('CADENCE', True, BLUE)
    surface.blit(label, label.get_rect(center=(x, y - 58)))


def draw_cadence_learning_hud():

    box = pygame.Surface(
        (
            830,
            230
        ),
        pygame.SRCALPHA
    )

    box.fill(
        (
            4,
            9,
            15,
            215
        )
    )

    panel_x = WIDTH - 870
    panel_y = HEIGHT - 270

    screen.blit(
        box,
        (
            panel_x,
            panel_y
        )
    )

    lines = [
        (
            "CADENCE // OFFICIAL BRAIN "
            f"{CADENCE_VERSION}",
            BLUE
        ),
        (
            f"GOAL: {cadence_goal_text}   "
            f"ACTION: {cadence_action}",
            WHITE
        ),
        (
            f"DECISIONS: {cadence_decisions}   "
            f"LAST REWARD: {cadence_last_reward:+.2f}   "
            f"SESSION KILLS: {cadence_kills}",
            YELLOW
        ),
        (
            f"RUN: {int(training_stats['total_runs']) + 1}   "
            f"SURVIVAL: {run_elapsed:0.1f}s   "
            f"AVG: {cadence_average_survival():0.1f}s",
            WHITE
        ),
        (
            f"BEST AREA: {int(training_stats['best_area'])}   "
            f"BEST SCORE: {int(training_stats['best_score'])}   "
            f"CLEARS: {int(training_stats['total_area_clears'])}",
            GREEN
        )
    ]

    line_y = panel_y + 16

    for line_text, line_color in lines:

        line_surface = font_small.render(
            line_text,
            True,
            line_color
        )

        screen.blit(
            line_surface,
            (
                panel_x + 24,
                line_y
            )
        )

        line_y += 41



# ============================================================
# DIFFICULTY
# ============================================================

def get_zombie_stats():

    if area_number == 1:

        return {
            "health": 75,
            "speed_min": int(65 * WORLD_SPEED_SCALE),
            "speed_max": int(90 * WORLD_SPEED_SCALE),
            "damage": 10
        }

    elif area_number == 2:

        return {
            "health": 100,
            "speed_min": int(78 * WORLD_SPEED_SCALE),
            "speed_max": int(108 * WORLD_SPEED_SCALE),
            "damage": 12
        }

    else:

        extra = area_number - 2

        return {
            "health": 100 + extra * 20,
            "speed_min": int((78 + extra * 4) * WORLD_SPEED_SCALE),
            "speed_max": int((108 + extra * 5) * WORLD_SPEED_SCALE),
            "damage": min(
                25,
                12 + extra * 2
            )
        }

# Native 1080p gameplay scale. Speeds are increased so the larger arena
# keeps the same arcade pacing as the earlier 1280x720 build.
WORLD_SPEED_SCALE = 1.50

# ============================================================
# CREATE ZOMBIE
# ============================================================

def create_zombie():

    stats = get_zombie_stats()

    # Choose zombie type
    zombie_type = "NORMAL"

    # Area 2+: 20% runners
    # Area 3+: 10% tanks + 20% runners
    type_roll = random.random()

    if area_number >= 3 and type_roll < 0.10:
        zombie_type = "TANK"

    elif area_number >= 2:

        runner_limit = (
            0.30 if area_number >= 3
            else 0.20
        )

        if type_roll < runner_limit:
            zombie_type = "RUNNER"

    side = random.choice(
        ["top", "bottom", "left", "right"]
    )

    margin = 30

    if side == "top":

        x = random.randint(
            ARENA_LEFT + margin,
            ARENA_RIGHT - margin
        )

        y = ARENA_TOP + margin

    elif side == "bottom":

        x = random.randint(
            ARENA_LEFT + margin,
            ARENA_RIGHT - margin
        )

        y = ARENA_BOTTOM - margin

    elif side == "left":

        x = ARENA_LEFT + margin

        y = random.randint(
            ARENA_TOP + margin,
            ARENA_BOTTOM - margin
        )

    else:

        x = ARENA_RIGHT - margin

        y = random.randint(
            ARENA_TOP + margin,
            ARENA_BOTTOM - margin
        )

    health = stats["health"]

    zombie_speed = random.uniform(
        stats["speed_min"],
        stats["speed_max"]
    )

    zombie_radius = 15
    zombie_damage = stats["damage"]
    score_value = 100

    # Runner zombie stats
    if zombie_type == "RUNNER":

        health = max(
            1,
            int(health * 0.60)
        )

        zombie_speed *= 1.65
        zombie_radius = 12
        score_value = 125

    # Tank zombie stats
    elif zombie_type == "TANK":

        health = int(health * 2.50)
        zombie_speed *= 0.55
        zombie_radius = 22

        zombie_damage = min(
            40,
            int(zombie_damage * 1.65)
        )

        score_value = 250

    zombies.append({
        "x": float(x),
        "y": float(y),

        "radius": zombie_radius,
        "type": zombie_type,

        "speed": zombie_speed,
        "damage": zombie_damage,
        "score_value": score_value,

        "health": health,
        "max_health": health,

        "hit_flash": 0,
        "avoid_direction": random.choice([-1, 1])
    })

# ============================================================
# DROPS
# ============================================================

def try_spawn_drop(x, y):

    roll = random.random()

    # 6% machine gun
    if roll < 0.06:

        drops.append({
            "x": x,
            "y": y,
            "type": "MACHINE GUN"
        })

    # 4% flamethrower
    elif roll < 0.10:

        drops.append({
            "x": x,
            "y": y,
            "type": "FLAMETHROWER"
        })
    # 5% medkit
    elif roll < 0.15:

        drops.append({
            "x": x,
            "y": y,
            "type": "MEDKIT"
        })

# ============================================================
# PICKUP WEAPON
# ============================================================

def pickup_weapon(drop):

    global current_weapon
    global special_ammo
    global player_health

    if drop["type"] == "MACHINE GUN":

        current_weapon = "MACHINE GUN"
        special_ammo = 250

    elif drop["type"] == "FLAMETHROWER":

        current_weapon = "FLAMETHROWER"
        special_ammo = 180

    elif drop["type"] == "MEDKIT":

        player_health += 30

        if player_health > max_player_health:
            player_health = max_player_health

# ============================================================
# SHOOT
# ============================================================

def shoot_bullet(mouse_pos, weapon):

    global muzzle_flash_timer

    mx, my = mouse_pos

    angle = math.atan2(
        my - player_y,
        mx - player_x
    )

    dx = math.cos(angle)
    dy = math.sin(angle)

    if weapon == "RIFLE":
        damage = 25
    else:
        damage = 18

    bullets.append({
        "x": player_x + dx * 38,
        "y": player_y + dy * 38,

        "dx": dx,
        "dy": dy,

        "radius": 4,
        "damage": damage
    })

    muzzle_flash_timer = muzzle_flash_duration

# ============================================================
# FLAMETHROWER
# ============================================================

def fire_flame(mouse_pos):

    mx, my = mouse_pos

    angle = math.atan2(
        my - player_y,
        mx - player_x
    )

    angle += random.uniform(
        -0.18,
        0.18
    )

    dx = math.cos(angle)
    dy = math.sin(angle)

    flames.append({
        "x": player_x + dx * 35,
        "y": player_y + dy * 35,

        "dx": dx,
        "dy": dy,

        "speed": random.uniform(
            300,
            420
        ),

        "life": random.uniform(
            0.25,
            0.45
        ),

        "radius": random.randint(
            6,
            11
        )
    })

# ============================================================
# GRAPHICS HELPERS
# ============================================================

def draw_soft_glow(surface, color, x, y, radius, alpha=70):

    glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)

    center = radius * 2

    pygame.draw.circle(
        glow,
        (*color, max(10, alpha // 3)),
        (center, center),
        int(radius * 1.55)
    )

    pygame.draw.circle(
        glow,
        (*color, alpha),
        (center, center),
        radius
    )

    surface.blit(
        glow,
        (int(x - center), int(y - center))
    )

def draw_tile(surface, rect, base_color, edge_color):

    pygame.draw.rect(surface, base_color, rect)
    pygame.draw.line(surface, edge_color, rect.topleft, rect.topright, 1)
    pygame.draw.line(surface, edge_color, rect.topleft, rect.bottomleft, 1)

    # Small deterministic wear marks
    if (rect.x // max(1, rect.width) + rect.y // max(1, rect.height)) % 4 == 0:
        pygame.draw.line(
            surface,
            tuple(max(0, c - 12) for c in base_color),
            (rect.x + 8, rect.y + 12),
            (rect.x + rect.width - 10, rect.y + rect.height - 8),
            1
        )

# ============================================================
# DRAW PLAYER
# ============================================================

def draw_player(surface, x, y, mouse_pos):

    mx, my = mouse_pos

    angle = math.atan2(
        my - y,
        mx - x
    )

    dx = math.cos(angle)
    dy = math.sin(angle)

    if player_invulnerable:

        if int(
            pygame.time.get_ticks() / 70
        ) % 2 == 0:

            return

    # Soft blue player glow and a stronger ground shadow
    draw_soft_glow(
        surface,
        (70, 150, 210),
        x,
        y,
        30,
        32
    )

    pygame.draw.ellipse(
        surface,
        (5, 7, 7),
        (
            int(x - 20),
            int(y + 10),
            40,
            16
        )
    )

    # Boots
    pygame.draw.rect(
        surface,
        (33, 42, 32),
        (int(x - 12), int(y + 8), 8, 13),
        border_radius=2
    )

    pygame.draw.rect(
        surface,
        (33, 42, 32),
        (int(x + 4), int(y + 8), 8, 13),
        border_radius=2
    )

    # Body / armor
    pygame.draw.rect(
        surface,
        (78, 105, 67),
        (int(x - 15), int(y - 10), 30, 27),
        border_radius=5
    )

    pygame.draw.rect(
        surface,
        (44, 62, 43),
        (int(x - 10), int(y - 6), 20, 18),
        border_radius=3
    )

    # Vest pouches
    pygame.draw.rect(surface, (95, 105, 70), (int(x - 8), int(y + 2), 6, 7), border_radius=1)
    pygame.draw.rect(surface, (95, 105, 70), (int(x + 2), int(y + 2), 6, 7), border_radius=1)

    # Head + helmet
    pygame.draw.circle(
        surface,
        SKIN,
        (int(x), int(y - 17)),
        10
    )

    pygame.draw.arc(
        surface,
        (47, 65, 43),
        (int(x - 12), int(y - 29), 24, 20),
        math.pi,
        math.pi * 2,
        9
    )

    pygame.draw.line(
        surface,
        (100, 115, 88),
        (int(x - 9), int(y - 22)),
        (int(x + 9), int(y - 22)),
        2
    )

    gun_length = 36
    gun_width = 7
    gun_color = GUN

    if current_weapon == "MACHINE GUN":
        gun_length = 43
        gun_width = 9
        gun_color = (48, 55, 61)

    elif current_weapon == "FLAMETHROWER":
        gun_length = 45
        gun_width = 10
        gun_color = (80, 65, 45)

    gun_start_x = x + dx * 4
    gun_start_y = y + dy * 4
    gun_end_x = x + dx * gun_length
    gun_end_y = y + dy * gun_length

    # Arms
    pygame.draw.line(
        surface,
        (164, 126, 90),
        (int(x - dy * 7), int(y + dx * 7)),
        (int(x + dx * 15 - dy * 4), int(y + dy * 15 + dx * 4)),
        5
    )

    pygame.draw.line(
        surface,
        (164, 126, 90),
        (int(x + dy * 7), int(y - dx * 7)),
        (int(x + dx * 15 + dy * 4), int(y + dy * 15 - dx * 4)),
        5
    )

    pygame.draw.line(
        surface,
        gun_color,
        (int(gun_start_x), int(gun_start_y)),
        (int(gun_end_x), int(gun_end_y)),
        gun_width
    )

    pygame.draw.line(
        surface,
        (125, 130, 126),
        (int(gun_start_x), int(gun_start_y)),
        (int(gun_end_x), int(gun_end_y)),
        2
    )

    if muzzle_flash_timer > 0:

        flash_x = x + dx * (gun_length + 7)
        flash_y = y + dy * (gun_length + 7)

        draw_soft_glow(
            surface,
            ORANGE,
            flash_x,
            flash_y,
            15,
            55
        )

        pygame.draw.circle(
            surface,
            YELLOW,
            (int(flash_x), int(flash_y)),
            random.randint(4, 7)
        )

# ============================================================
# DRAW ZOMBIE
# ============================================================

def draw_zombie(surface, zombie):

    x = float(zombie["x"])
    y = float(zombie["y"])

    zombie_type = zombie.get(
        "type",
        "NORMAL"
    )

    # Face toward the player.
    angle = math.atan2(
        player_y - y,
        player_x - x
    )

    forward_x = math.cos(angle)
    forward_y = math.sin(angle)

    right_x = -forward_y
    right_y = forward_x

    is_runner = (
        zombie_type == "RUNNER"
    )

    is_tank = (
        zombie_type == "TANK"
    )

    is_boss = (
        zombie_type == "BOSS"
    )

    if is_boss:
        body_length = 54
        body_width = 50
        head_radius = 19
        arm_length = 38
        arm_width = 15
        leg_length = 25
        skin_color = (104, 118, 78)
        shirt_color = (94, 35, 37)
        armor_color = (132, 50, 52)
        health_bar_width = 62

    elif is_tank:
        body_length = 42
        body_width = 40
        head_radius = 15
        arm_length = 31
        arm_width = 12
        leg_length = 21
        skin_color = (91, 109, 77)
        shirt_color = (64, 67, 70)
        armor_color = (98, 103, 108)
        health_bar_width = 48

    elif is_runner:
        body_length = 29
        body_width = 23
        head_radius = 9
        arm_length = 26
        arm_width = 7
        leg_length = 18
        skin_color = (126, 153, 88)
        shirt_color = (144, 67, 45)
        armor_color = None
        health_bar_width = 30

    else:
        body_length = 33
        body_width = 29
        head_radius = 11
        arm_length = 27
        arm_width = 8
        leg_length = 19
        skin_color = ZOMBIE_SKIN
        shirt_color = ZOMBIE_SHIRT
        armor_color = None
        health_bar_width = 36

    if zombie["hit_flash"] > 0:
        shirt_color = WHITE
        skin_color = WHITE

    # Shadow gives the character more depth.
    shadow_w = int(
        body_width * 1.45
    )

    shadow_h = int(
        body_length * 0.42
    )

    pygame.draw.ellipse(
        surface,
        (6, 8, 7),
        (
            int(x - shadow_w / 2 + 5),
            int(y + body_length * 0.14),
            shadow_w,
            shadow_h
        )
    )

    # Feet / legs point backwards.
    for side in (-1, 1):

        hip_x = (
            x -
            forward_x * body_length * 0.24 +
            right_x * side * body_width * 0.22
        )

        hip_y = (
            y -
            forward_y * body_length * 0.24 +
            right_y * side * body_width * 0.22
        )

        foot_x = (
            hip_x -
            forward_x * leg_length
        )

        foot_y = (
            hip_y -
            forward_y * leg_length
        )

        pygame.draw.line(
            surface,
            (45, 51, 43),
            (
                int(hip_x),
                int(hip_y)
            ),
            (
                int(foot_x),
                int(foot_y)
            ),
            8 if is_tank
            else 11 if is_boss
            else 6
        )

        pygame.draw.circle(
            surface,
            (33, 37, 33),
            (
                int(foot_x),
                int(foot_y)
            ),
            5 if not is_boss
            else 8
        )

    # Rotated torso polygon.
    half_w = body_width / 2
    half_l = body_length / 2

    torso_points = []

    for longitudinal, lateral in (
        (half_l, -half_w),
        (half_l, half_w),
        (-half_l, half_w * 0.78),
        (-half_l, -half_w * 0.78)
    ):

        px = (
            x +
            forward_x * longitudinal +
            right_x * lateral
        )

        py = (
            y +
            forward_y * longitudinal +
            right_y * lateral
        )

        torso_points.append(
            (
                int(px),
                int(py)
            )
        )

    pygame.draw.polygon(
        surface,
        shirt_color,
        torso_points
    )

    pygame.draw.polygon(
        surface,
        (38, 45, 39),
        torso_points,
        2
    )

    # Heavy zombies get visible armor plating.
    if armor_color is not None:

        armor_center_x = (
            x +
            forward_x * 4
        )

        armor_center_y = (
            y +
            forward_y * 4
        )

        armor_l = body_length * 0.45
        armor_w = body_width * 0.62

        armor_points = []

        for longitudinal, lateral in (
            (armor_l, -armor_w / 2),
            (armor_l, armor_w / 2),
            (-armor_l, armor_w / 2),
            (-armor_l, -armor_w / 2)
        ):

            px = (
                armor_center_x +
                forward_x * longitudinal +
                right_x * lateral
            )

            py = (
                armor_center_y +
                forward_y * longitudinal +
                right_y * lateral
            )

            armor_points.append(
                (
                    int(px),
                    int(py)
                )
            )

        pygame.draw.polygon(
            surface,
            WHITE
            if zombie["hit_flash"] > 0
            else armor_color,
            armor_points
        )

        pygame.draw.polygon(
            surface,
            (45, 44, 43),
            armor_points,
            2
        )

    # Arms reach forward, making the zombie silhouette clearer.
    shoulder_forward = body_length * 0.20
    shoulder_side = body_width * 0.54

    for side in (-1, 1):

        shoulder_x = (
            x +
            forward_x * shoulder_forward +
            right_x * side * shoulder_side
        )

        shoulder_y = (
            y +
            forward_y * shoulder_forward +
            right_y * side * shoulder_side
        )

        hand_x = (
            shoulder_x +
            forward_x * arm_length +
            right_x * side * (
                4 if is_runner
                else 8
            )
        )

        hand_y = (
            shoulder_y +
            forward_y * arm_length +
            right_y * side * (
                4 if is_runner
                else 8
            )
        )

        pygame.draw.line(
            surface,
            skin_color,
            (
                int(shoulder_x),
                int(shoulder_y)
            ),
            (
                int(hand_x),
                int(hand_y)
            ),
            arm_width
        )

        pygame.draw.circle(
            surface,
            skin_color,
            (
                int(hand_x),
                int(hand_y)
            ),
            max(
                4,
                arm_width // 2
            )
        )

    # Head sits toward the front of the torso.
    head_x = (
        x +
        forward_x *
        (
            body_length * 0.56
        )
    )

    head_y = (
        y +
        forward_y *
        (
            body_length * 0.56
        )
    )

    pygame.draw.circle(
        surface,
        skin_color,
        (
            int(head_x),
            int(head_y)
        ),
        head_radius
    )

    # Dark skull outline.
    pygame.draw.circle(
        surface,
        (40, 48, 39),
        (
            int(head_x),
            int(head_y)
        ),
        head_radius,
        2
    )

    # Glowing eyes.
    eye_side = (
        7 if is_boss
        else 5 if is_tank
        else 3
    )

    eye_forward = (
        head_radius * 0.35
    )

    eye_color = (
        YELLOW
        if is_boss
        else RED
    )

    for side in (-1, 1):

        eye_x = (
            head_x +
            forward_x * eye_forward +
            right_x * side * eye_side
        )

        eye_y = (
            head_y +
            forward_y * eye_forward +
            right_y * side * eye_side
        )

        pygame.draw.circle(
            surface,
            eye_color,
            (
                int(eye_x),
                int(eye_y)
            ),
            3 if is_boss
            else 2
        )

    # Boss charge aura.
    if (
        is_boss
        and
        zombie.get(
            "charge_duration",
            0
        ) > 0
    ):

        pulse = int(
            55 +
            math.sin(
                pygame.time.get_ticks()
                * 0.025
            ) * 7
        )

        pygame.draw.circle(
            surface,
            ORANGE,
            (
                int(x),
                int(y)
            ),
            pulse,
            3
        )

    # Local health bar.
    if not is_boss:

        health_percent = max(
            0,
            zombie["health"] /
            zombie["max_health"]
        )

        bar_x = (
            int(x) -
            health_bar_width // 2
        )

        bar_y = (
            int(y) -
            int(body_length * 0.85) -
            24
        )

        pygame.draw.rect(
            surface,
            DARK_RED,
            (
                bar_x,
                bar_y,
                health_bar_width,
                6
            )
        )

        pygame.draw.rect(
            surface,
            GREEN,
            (
                bar_x,
                bar_y,
                int(
                    health_bar_width *
                    health_percent
                ),
                6
            )
        )


# ============================================================
# DRAW BOSS HUD
# ============================================================

def draw_boss_hud():

    boss = None

    for zombie in zombies:

        if zombie.get(
            "type"
        ) == "BOSS":

            boss = zombie
            break

    if boss is None:
        return

    bar_width = 560
    bar_height = 24

    bar_x = (
        WIDTH // 2 -
        bar_width // 2
    )

    bar_y = 48

    health_percent = max(
        0,
        boss["health"] /
        boss["max_health"]
    )

    title = font_medium.render(
        "THE BRUTE",
        True,
        RED
    )

    title_rect = title.get_rect(
        center=(
            WIDTH // 2,
            28
        )
    )

    screen.blit(
        title,
        title_rect
    )

    pygame.draw.rect(
        screen,
        (45, 12, 12),
        (
            bar_x - 3,
            bar_y - 3,
            bar_width + 6,
            bar_height + 6
        )
    )

    pygame.draw.rect(
        screen,
        DARK_RED,
        (
            bar_x,
            bar_y,
            bar_width,
            bar_height
        )
    )

    pygame.draw.rect(
        screen,
        RED,
        (
            bar_x,
            bar_y,
            int(
                bar_width *
                health_percent
            ),
            bar_height
        )
    )

    hp_text = font_small.render(
        (
            f"{max(0, int(boss['health']))}"
            f" / {boss['max_health']} HP"
        ),
        True,
        WHITE
    )

    hp_rect = hp_text.get_rect(
        center=(
            WIDTH // 2,
            bar_y + bar_height // 2
        )
    )

    screen.blit(
        hp_text,
        hp_rect
    )

# ============================================================
# DRAW DROP
# ============================================================

def draw_drop(surface, drop):

    x = int(drop["x"])
    y = int(drop["y"])

    pulse = int(
        4 +
        math.sin(
            pygame.time.get_ticks()
            * 0.008
        ) * 2
    )

    if drop["type"] == "MACHINE GUN":

        pygame.draw.circle(
            surface,
            BLUE,
            (x, y),
            18 + pulse,
            2
        )

        pygame.draw.rect(
            surface,
            (50, 55, 58),
            (
                x - 17,
                y - 4,
                34,
                8
            )
        )

        pygame.draw.rect(
            surface,
            (110, 120, 125),
            (
                x + 8,
                y - 2,
                18,
                4
            )
        )

        pygame.draw.rect(
            surface,
            (60, 65, 68),
            (
                x - 4,
                y + 3,
                7,
                10
            )
        )

    elif drop["type"] == "FLAMETHROWER":

        pygame.draw.circle(
            surface,
            ORANGE,
            (x, y),
            18 + pulse,
            2
        )

        pygame.draw.rect(
            surface,
            FIRE_RED,
            (
                x - 14,
                y - 8,
                15,
                16
            )
        )

        pygame.draw.rect(
            surface,
            (70, 70, 65),
            (
                x - 2,
                y - 4,
                27,
                7
            )
        )

    elif drop["type"] == "MEDKIT":

        # Glowing pickup circle
        pygame.draw.circle(
            surface,
            RED,
            (x, y),
            18 + pulse,
            2
        )

        # White medical box
        pygame.draw.rect(
            surface,
            WHITE,
            (
                x - 13,
                y - 11,
                26,
                22
            )
        )

        # Red medical cross
        pygame.draw.rect(
            surface,
            RED,
            (
                x - 3,
                y - 8,
                6,
                16
            )
        )

        pygame.draw.rect(
            surface,
            RED,
            (
                x - 8,
                y - 3,
                16,
                6
            )
        )

# ============================================================
# CROSSHAIR
# ============================================================

def draw_crosshair(surface, mouse_pos):

    mx, my = mouse_pos

    size = 10
    gap = 4

    pygame.draw.line(
        surface,
        WHITE,
        (mx - size, my),
        (mx - gap, my),
        2
    )

    pygame.draw.line(
        surface,
        WHITE,
        (mx + gap, my),
        (mx + size, my),
        2
    )

    pygame.draw.line(
        surface,
        WHITE,
        (mx, my - size),
        (mx, my - gap),
        2
    )

    pygame.draw.line(
        surface,
        WHITE,
        (mx, my + gap),
        (mx, my + size),
        2
    )

    pygame.draw.circle(
        surface,
        WHITE,
        (mx, my),
        2
    )

# ============================================================
# AREA 1
# ============================================================

def draw_dead_streets():

    # Dirt courtyard inspired by classic top-down arcade arenas.
    pygame.draw.rect(
        screen,
        (55, 49, 39),
        (ARENA_LEFT, ARENA_TOP, ARENA_RIGHT - ARENA_LEFT, ARENA_BOTTOM - ARENA_TOP)
    )

    # Dark dirt quadrants
    dirt = (46, 42, 34)
    pygame.draw.rect(screen, dirt, (ARENA_LEFT + 20, ARENA_TOP + 20, 370, 220))
    pygame.draw.rect(screen, dirt, (ARENA_RIGHT - 390, ARENA_TOP + 20, 370, 220))
    pygame.draw.rect(screen, dirt, (ARENA_LEFT + 20, ARENA_BOTTOM - 240, 370, 220))
    pygame.draw.rect(screen, dirt, (ARENA_RIGHT - 390, ARENA_BOTTOM - 240, 370, 220))

    tile_size = 38
    stone_a = (137, 139, 127)
    stone_b = (122, 125, 115)
    edge = (90, 93, 86)

    # Horizontal stone road
    road_y = HEIGHT // 2 - 95
    for y in range(road_y, road_y + 190, tile_size):
        for x in range(ARENA_LEFT, ARENA_RIGHT, tile_size):
            c = stone_a if ((x // tile_size) + (y // tile_size)) % 2 == 0 else stone_b
            draw_tile(screen, pygame.Rect(x, y, tile_size, tile_size), c, edge)

    # Vertical stone road
    road_x = WIDTH // 2 - 100
    for y in range(ARENA_TOP, ARENA_BOTTOM, tile_size):
        for x in range(road_x, road_x + 200, tile_size):
            c = stone_a if ((x // tile_size) + (y // tile_size)) % 2 == 0 else stone_b
            draw_tile(screen, pygame.Rect(x, y, tile_size, tile_size), c, edge)

    # Central fountain / monument
    cx = WIDTH // 2
    cy = HEIGHT // 2

    # Fountain is now a SOLID barrier.
    pygame.draw.circle(screen, (48, 48, 45), (cx + 9, cy + 12), 78)
    pygame.draw.circle(screen, (92, 92, 86), (cx, cy), 75)
    pygame.draw.circle(screen, (176, 176, 165), (cx, cy), 70)
    pygame.draw.circle(screen, (150, 150, 140), (cx, cy), 67)
    pygame.draw.circle(screen, (112, 115, 110), (cx, cy), 52)
    pygame.draw.circle(screen, (179, 182, 174), (cx, cy), 40)
    pygame.draw.circle(screen, (118, 135, 138), (cx, cy), 30)
    pygame.draw.circle(screen, (198, 198, 186), (cx, cy - 5), 19)

    # Cracked / broken tiles around fountain
    pygame.draw.polygon(screen, dirt, [(cx + 75, cy - 65), (cx + 110, cy - 60), (cx + 102, cy - 22), (cx + 82, cy - 35)])
    pygame.draw.polygon(screen, dirt, [(cx - 120, cy + 40), (cx - 95, cy + 28), (cx - 80, cy + 60), (cx - 110, cy + 74)])

    # Small debris
    debris = [
        (170, 180, 24, 10),
        (1040, 175, 30, 12),
        (190, 525, 28, 10),
        (1025, 520, 34, 11),
        (340, 125, 18, 8),
        (900, 600, 22, 8),
        (1450, 180, 30, 10),
        (1560, 790, 35, 12),
        (380, 840, 28, 10),
    ]

    for dx, dy, dw, dh in debris:
        pygame.draw.rect(screen, (94, 91, 80), (dx, dy, dw, dh))
        pygame.draw.line(screen, (55, 52, 45), (dx, dy), (dx + dw, dy + dh), 2)

# ============================================================
# AREA 2+
# ============================================================

def draw_industrial_yard():

    theme = area_number % 4

    if theme == 2:
        floor_color = (45, 46, 47)
        slab_a = (68, 70, 73)
        slab_b = (60, 62, 65)
        accent = (150, 122, 40)
    elif theme == 3:
        floor_color = (38, 43, 40)
        slab_a = (64, 69, 63)
        slab_b = (55, 61, 55)
        accent = (104, 90, 54)
    elif theme == 0:
        floor_color = (46, 37, 35)
        slab_a = (70, 57, 53)
        slab_b = (61, 49, 46)
        accent = (150, 75, 48)
    else:
        floor_color = (35, 39, 43)
        slab_a = (57, 63, 68)
        slab_b = (50, 55, 60)
        accent = (70, 118, 135)

    pygame.draw.rect(
        screen,
        floor_color,
        (ARENA_LEFT, ARENA_TOP, ARENA_RIGHT - ARENA_LEFT, ARENA_BOTTOM - ARENA_TOP)
    )

    slab = 64

    for y in range(ARENA_TOP, ARENA_BOTTOM, slab):
        for x in range(ARENA_LEFT, ARENA_RIGHT, slab):
            c = slab_a if ((x // slab) + (y // slab)) % 2 == 0 else slab_b
            draw_tile(screen, pygame.Rect(x, y, slab, slab), c, (42, 44, 46))

    # Central lane
    pygame.draw.rect(screen, (31, 33, 35), (ARENA_LEFT, HEIGHT // 2 - 72, ARENA_RIGHT - ARENA_LEFT, 144))

    for x in range(ARENA_LEFT + 30, ARENA_RIGHT - 20, 72):
        pygame.draw.rect(screen, accent, (x, HEIGHT // 2 - 5, 38, 10))

    # Crates and industrial props.
    # These exact positions are also used by the collision system.
    crates = get_crate_positions()

    for crate_x, crate_y in crates:
        # Solid crate shadow + raised wooden box.
        pygame.draw.rect(screen, (42, 34, 27), (crate_x + 7, crate_y + 9, 40, 40))
        pygame.draw.rect(screen, (117, 89, 56), (crate_x, crate_y, 38, 38))
        pygame.draw.rect(screen, (176, 137, 87), (crate_x, crate_y, 38, 38), 4)
        pygame.draw.line(screen, (151, 116, 72), (crate_x, crate_y), (crate_x + 38, crate_y + 38), 2)
        pygame.draw.line(screen, (151, 116, 72), (crate_x + 38, crate_y), (crate_x, crate_y + 38), 2)

    # Glowing lamps
    for lx, ly in [(115, 115), (WIDTH - 115, 115), (115, HEIGHT - 115), (WIDTH - 115, HEIGHT - 115)]:
        draw_soft_glow(screen, accent, lx, ly, 22, 35)
        pygame.draw.circle(screen, (215, 205, 150), (lx, ly), 4)

# ============================================================
# WORLD
# ============================================================

def draw_world():

    screen.fill(BACKGROUND)

    if area_number == 1:
        draw_dead_streets()
    else:
        draw_industrial_yard()

    # Heavy arena frame
    pygame.draw.rect(
        screen,
        (20, 24, 23),
        (ARENA_LEFT - 7, ARENA_TOP - 7, ARENA_RIGHT - ARENA_LEFT + 14, ARENA_BOTTOM - ARENA_TOP + 14),
        7
    )

    pygame.draw.rect(
        screen,
        (99, 108, 101),
        (ARENA_LEFT, ARENA_TOP, ARENA_RIGHT - ARENA_LEFT, ARENA_BOTTOM - ARENA_TOP),
        2
    )

    # Screen-edge vignette
    vignette = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.rect(vignette, (0, 0, 0, 75), (0, 0, WIDTH, 28))
    pygame.draw.rect(vignette, (0, 0, 0, 75), (0, HEIGHT - 28, WIDTH, 28))
    pygame.draw.rect(vignette, (0, 0, 0, 55), (0, 0, 28, HEIGHT))
    pygame.draw.rect(vignette, (0, 0, 0, 55), (WIDTH - 28, 0, 28, HEIGHT))
    screen.blit(vignette, (0, 0))

# ============================================================
# EXIT
# ============================================================

def draw_exit():

    pulse = (
        math.sin(
            pygame.time.get_ticks()
            * 0.006
        ) + 1
    ) / 2

    outer_radius = int(
        30 +
        pulse * 8
    )

    pygame.draw.circle(
        screen,
        DARK_GREEN,
        (
            int(exit_x),
            int(exit_y)
        ),
        outer_radius
    )

    pygame.draw.circle(
        screen,
        GREEN,
        (
            int(exit_x),
            int(exit_y)
        ),
        25,
        4
    )

    pygame.draw.circle(
        screen,
        WHITE,
        (
            int(exit_x),
            int(exit_y)
        ),
        8
    )

    exit_text = font_small.render(
        "EXIT",
        True,
        GREEN
    )

    exit_rect = exit_text.get_rect(
        center=(
            int(exit_x),
            int(exit_y + 48)
        )
    )

    screen.blit(
        exit_text,
        exit_rect
    )

# ============================================================
# NEXT AREA
# ============================================================

def start_next_area():

    global area_number
    global round_number

    global player_x
    global player_y

    global zombies
    global bullets
    global flames
    global drops

    global zombies_to_spawn
    global zombies_spawned
    global round_kills

    global spawn_timer
    global spawn_delay

    global round_complete
    global exit_active

    global transition_active
    global transition_timer

    global boss_spawned
    global boss_defeated
    global boss_intro_timer

    area_number += 1
    round_number += 1

    player_x, player_y = get_player_spawn()

    zombies = []
    bullets = []
    flames = []
    drops = []

    round_kills = 0
    zombies_spawned = 0

    if area_number == 2:

        zombies_to_spawn = 25
        spawn_delay = 0.80

    else:

        zombies_to_spawn = (
            25 +
            (area_number - 2) * 10
        )

        spawn_delay = max(
            0.35,
            0.80 -
            (area_number - 2) * 0.05
        )

    spawn_timer = 1.5

    round_complete = False
    exit_active = False

    transition_active = True
    transition_timer = transition_duration

    boss_spawned = False
    boss_defeated = False
    boss_intro_timer = 0

    cadence_reset_navigation()
    cadence_save_official_brain()

# ============================================================
# RESTART GAME
# ============================================================

def restart_game():

    global area_number
    global round_number

    global player_x
    global player_y
    global player_health

    global player_invulnerable
    global player_invulnerable_timer
    global player_hit_flash

    global current_weapon
    global special_ammo

    global bullets
    global flames
    global drops
    global zombies

    global score
    global total_kills
    global round_kills

    global zombies_to_spawn
    global zombies_spawned

    global spawn_timer
    global spawn_delay

    global round_complete
    global exit_active

    global transition_active
    global transition_timer

    global boss_spawned
    global boss_defeated
    global boss_intro_timer

    global cadence_reward_buffer
    global cadence_decision_timer
    global cadence_action
    global cadence_goal_text
    global cadence_target
    global game_over_timer
    global cadence_terminal_sent
    global cadence_has_pending_action

    global cadence_emergency_timer
    global cadence_stuck_timer
    global cadence_unstuck_timer
    global cadence_path
    global cadence_path_goal
    global cadence_path_replan_timer
    global cadence_escape_waypoint
    global cadence_escape_replan_timer

    global run_elapsed
    global run_recorded

    global game_over

    area_number = 1
    round_number = 1

    player_x, player_y = get_player_spawn()

    player_health = max_player_health

    player_invulnerable = False
    player_invulnerable_timer = 0
    player_hit_flash = 0

    current_weapon = "RIFLE"
    special_ammo = 0

    bullets = []
    flames = []
    drops = []
    zombies = []

    score = 0
    total_kills = 0
    round_kills = 0

    zombies_to_spawn = 15
    zombies_spawned = 0

    spawn_timer = 0
    spawn_delay = 1.0

    round_complete = False
    exit_active = False

    transition_active = False
    transition_timer = 0

    boss_spawned = False
    boss_defeated = False
    boss_intro_timer = 0

    cadence_reward_buffer = 0.0
    cadence_decision_timer = 0.0
    cadence_action = "KITE"
    cadence_goal_text = "SCANNING"
    cadence_target = None
    game_over_timer = 0.0
    cadence_terminal_sent = False

    # terminal feedback clears the previous episode's pending action.
    # If R is pressed before terminal feedback, start clean.
    cadence_has_pending_action = False

    cadence_emergency_timer = 0.0
    cadence_stuck_timer = 0.0
    cadence_unstuck_timer = 0.0
    cadence_path = []
    cadence_path_goal = None
    cadence_path_replan_timer = 0.0
    cadence_escape_waypoint = None
    cadence_escape_replan_timer = 0.0

    run_elapsed = 0.0
    run_recorded = False

    game_over = False

# ============================================================
# START
# ============================================================

pygame.mouse.set_visible(False)

cadence_load_training_stats()
cadence_load_official_brain()

running = True

# ============================================================
# GAME LOOP
# ============================================================

while running:

    dt = clock.tick(FPS) / 1000.0

    if not game_over:
        run_elapsed += dt

    if startup_overlay_timer > 0:
        startup_overlay_timer = max(
            0.0,
            startup_overlay_timer - dt
        )

    # --------------------------------------------------------
    # TIMERS
    # --------------------------------------------------------

    if fire_timer > 0:
        fire_timer -= dt

    if muzzle_flash_timer > 0:
        muzzle_flash_timer -= dt

    if player_invulnerable_timer > 0:

        player_invulnerable_timer -= dt

        if player_invulnerable_timer <= 0:

            player_invulnerable_timer = 0
            player_invulnerable = False

    if player_hit_flash > 0:
        player_hit_flash -= dt

    if boss_intro_timer > 0:
        boss_intro_timer -= dt

    for zombie in zombies:

        if zombie["hit_flash"] > 0:
            zombie["hit_flash"] -= dt

    # --------------------------------------------------------
    # EVENTS
    # --------------------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_r and game_over:
                restart_game()

    # --------------------------------------------------------
    # TRANSITION
    # --------------------------------------------------------

    if transition_active:

        transition_timer -= dt

        if transition_timer <= 0:
            transition_active = False

    # --------------------------------------------------------
    # CADENCE AUTONOMOUS CONTROL
    # --------------------------------------------------------

    update_cadence_ai(dt)

    # Return to rifle when special ammo is empty
    if (
        current_weapon != "RIFLE"
        and
        special_ammo <= 0
    ):

        current_weapon = "RIFLE"
        special_ammo = 0

    # --------------------------------------------------------
    # SPAWN ZOMBIES
    # --------------------------------------------------------

    if (
        not round_complete
        and
        not transition_active
        and
        not game_over
    ):

        if zombies_spawned < zombies_to_spawn:

            spawn_timer -= dt

            if spawn_timer <= 0:

                create_zombie()

                zombies_spawned += 1

                spawn_timer = spawn_delay

    # --------------------------------------------------------
    # UPDATE ZOMBIES
    # --------------------------------------------------------

    if not transition_active and not game_over:

        for zombie in zombies:

            zombie_type = zombie.get(
                "type",
                "NORMAL"
            )

            if zombie_type == "BOSS":

                # Boss charge now collides with solid map objects.
                if zombie["charge_duration"] > 0:

                    zombie["charge_duration"] -= dt

                    old_x = zombie["x"]
                    old_y = zombie["y"]

                    charge_step = (
                        zombie["charge_speed"] *
                        dt
                    )

                    new_x, new_y = (
                        move_circle_with_map_collision(
                            old_x,
                            old_y,
                            zombie["charge_dx"] *
                            charge_step,
                            zombie["charge_dy"] *
                            charge_step,
                            zombie["radius"]
                        )
                    )

                    moved = distance(
                        old_x,
                        old_y,
                        new_x,
                        new_y
                    )

                    zombie["x"] = new_x
                    zombie["y"] = new_y

                    # Smashing into the fountain/crate stops the charge.
                    if moved < charge_step * 0.35:
                        zombie["charge_duration"] = 0
                        zombie["charge_timer"] = 1.5

                else:

                    zombie["charge_timer"] -= dt

                    angle = math.atan2(
                        player_y - zombie["y"],
                        player_x - zombie["x"]
                    )

                    if zombie["charge_timer"] <= 0:

                        zombie["charge_dx"] = (
                            math.cos(angle)
                        )

                        zombie["charge_dy"] = (
                            math.sin(angle)
                        )

                        zombie["charge_duration"] = 0.72

                        zombie["charge_timer"] = (
                            random.uniform(
                                3.0,
                                4.3
                            )
                        )

                    else:

                        move_zombie_toward_player(
                            zombie,
                            zombie["speed"],
                            dt
                        )

            else:

                move_zombie_toward_player(
                    zombie,
                    zombie["speed"],
                    dt
                )

        # Keep zombies from stacking on top of each other.
        for i in range(len(zombies)):

            for j in range(i + 1, len(zombies)):

                zombie_a = zombies[i]
                zombie_b = zombies[j]

                dx = (
                    zombie_b["x"] -
                    zombie_a["x"]
                )

                dy = (
                    zombie_b["y"] -
                    zombie_a["y"]
                )

                dist = math.sqrt(
                    dx * dx +
                    dy * dy
                )

                minimum_distance = (
                    zombie_a["radius"] +
                    zombie_b["radius"] +
                    5
                )

                if 0 < dist < minimum_distance:

                    overlap = (
                        minimum_distance - dist
                    ) / 2

                    push_x = (
                        dx / dist
                    ) * overlap

                    push_y = (
                        dy / dist
                    ) * overlap

                    new_ax, new_ay = (
                        move_circle_with_map_collision(
                            zombie_a["x"],
                            zombie_a["y"],
                            -push_x,
                            -push_y,
                            zombie_a["radius"]
                        )
                    )

                    new_bx, new_by = (
                        move_circle_with_map_collision(
                            zombie_b["x"],
                            zombie_b["y"],
                            push_x,
                            push_y,
                            zombie_b["radius"]
                        )
                    )

                    zombie_a["x"] = new_ax
                    zombie_a["y"] = new_ay
                    zombie_b["x"] = new_bx
                    zombie_b["y"] = new_by

    # --------------------------------------------------------
    # ZOMBIE VS CADENCE
    # --------------------------------------------------------
       
    if not transition_active and not game_over:

        for zombie in zombies:

            if distance(
                player_x,
                player_y,
                zombie["x"],
                zombie["y"]
            ) < (
                player_radius +
                zombie["radius"]
            ):

                if not player_invulnerable:

                    player_health -= zombie["damage"]

                    player_health = max(
                        0,
                        player_health
                    )

                    player_invulnerable = True

                    player_invulnerable_timer = (
                        player_invulnerable_duration
                    )

                    player_hit_flash = 0.20

                    cadence_reward_buffer -= 2.5

                    # Immediate reflex: Cadence must move after being hit.
                    cadence_emergency_timer = 1.35
                    cadence_reset_navigation()
                    cadence_escape_waypoint = None
                    cadence_escape_replan_timer = 0.0

                    # Knock zombie away
                    push_angle = math.atan2(
                        zombie["y"] - player_y,
                        zombie["x"] - player_x
                    )

                    zombie["x"] += (
                        math.cos(push_angle) *
                        32
                    )

                    zombie["y"] += (
                        math.sin(push_angle) *
                        32
                    )

                    if player_health <= 0:
                        cadence_reward_buffer -= 15.0
                        cadence_deaths += 1
                        cadence_terminal_feedback()
                        cadence_record_run()
                        game_over = True
                        game_over_timer = 2.5

                    break

    # --------------------------------------------------------
    # UPDATE BULLETS
    # --------------------------------------------------------

    if not game_over:

        for bullet in bullets:

            bullet["x"] += (
                bullet["dx"] *
                bullet_speed *
                dt
            )

            bullet["y"] += (
                bullet["dy"] *
                bullet_speed *
                dt
            )

    # Bullets cannot pass through the fountain, crates, or walls.
    bullets = [
        bullet
        for bullet in bullets
        if not circle_hits_map(
            bullet["x"],
            bullet["y"],
            bullet["radius"]
        )
    ]

    # --------------------------------------------------------
    # UPDATE FLAMES
    # --------------------------------------------------------

    if not game_over:

        for flame in flames:

            flame["x"] += (
                flame["dx"] *
                flame["speed"] *
                dt
            )

            flame["y"] += (
                flame["dy"] *
                flame["speed"] *
                dt
            )

            flame["life"] -= dt
            flame["radius"] += 18 * dt

    # Fire also stops when it reaches a solid map object.
    for flame in flames:
        if circle_hits_map(
            flame["x"],
            flame["y"],
            max(3, flame["radius"] * 0.45)
        ):
            flame["life"] = 0

    flames = [
        flame
        for flame in flames
        if flame["life"] > 0
    ]

    # --------------------------------------------------------
    # BULLET VS ZOMBIE
    # --------------------------------------------------------

    bullets_to_remove = []
    zombies_to_remove = []

    if not game_over:

        for bullet in bullets:

            for zombie in zombies:

                if distance(
                    bullet["x"],
                    bullet["y"],
                    zombie["x"],
                    zombie["y"]
                ) < (
                    bullet["radius"] +
                    zombie["radius"]
                ):

                    zombie["health"] -= (
                        bullet["damage"]
                    )

                    zombie["hit_flash"] = 0.08

                    cadence_reward_buffer += 0.12
                    cadence_hits += 1

                    bullets_to_remove.append(
                        bullet
                    )

                    if zombie["health"] <= 0:

                        if zombie not in zombies_to_remove:

                            zombies_to_remove.append(
                                zombie
                            )

                    break

    # --------------------------------------------------------
    # FLAME VS ZOMBIE
    # --------------------------------------------------------

    if not game_over:

        for flame in flames:

            for zombie in zombies:

                if zombie in zombies_to_remove:
                    continue

                if distance(
                    flame["x"],
                    flame["y"],
                    zombie["x"],
                    zombie["y"]
                ) < (
                    flame["radius"] +
                    zombie["radius"]
                ):

                    zombie["health"] -= 4
                    zombie["hit_flash"] = 0.04

                    flame["life"] = 0

                    if zombie["health"] <= 0:

                        if zombie not in zombies_to_remove:

                            zombies_to_remove.append(
                                zombie
                            )

                    break

    # --------------------------------------------------------
    # REMOVE HIT BULLETS
    # --------------------------------------------------------

    for bullet in bullets_to_remove:

        if bullet in bullets:
            bullets.remove(bullet)

    # --------------------------------------------------------
    # REMOVE DEAD ZOMBIES
    # --------------------------------------------------------

    for zombie in zombies_to_remove:

        if zombie in zombies:

            death_x = zombie["x"]
            death_y = zombie["y"]

            zombies.remove(zombie)

            cadence_reward_buffer += (
                8.0
                if zombie.get("type") == "BOSS"
                else 4.0
            )
            cadence_kills += 1

            total_kills += 1

            if zombie.get(
                "type"
            ) != "BOSS":

                round_kills += 1

            score += (
                zombie.get(
                    "score_value",
                    100
                ) +
                (area_number - 1) * 25
            )

            if zombie.get(
                "type"
            ) == "BOSS":

                boss_defeated = True

                # Boss always leaves a medkit.
                drops.append({
                    "x": death_x,
                    "y": death_y,
                    "type": "MEDKIT"
                })

            else:

                try_spawn_drop(
                    death_x,
                    death_y
                )

    # --------------------------------------------------------
    # REMOVE OFFSCREEN BULLETS
    # --------------------------------------------------------

    bullets = [
        bullet
        for bullet in bullets
        if (
            ARENA_LEFT
            <= bullet["x"]
            <= ARENA_RIGHT
            and
            ARENA_TOP
            <= bullet["y"]
            <= ARENA_BOTTOM
        )
    ]

    # --------------------------------------------------------
    # PICKUPS
    # --------------------------------------------------------

    if not game_over:

        drops_to_remove = []

        for drop in drops:

            if distance(
                player_x,
                player_y,
                drop["x"],
                drop["y"]
            ) < pickup_radius:

                useful_pickup = True

                if drop["type"] == "MEDKIT" and player_health >= 88:
                    useful_pickup = False

                if (
                    drop["type"] in ("MACHINE GUN", "FLAMETHROWER")
                    and current_weapon != "RIFLE"
                    and special_ammo > 80
                ):
                    useful_pickup = False

                if useful_pickup:
                    was_health = player_health
                    pickup_type = drop["type"]

                    pickup_weapon(drop)

                    cadence_pickups += 1

                    if pickup_type == "MEDKIT":
                        cadence_reward_buffer += (
                            8.0
                            if was_health <= 45
                            else
                            5.5
                            if was_health <= 72
                            else
                            0.3
                        )
                    else:
                        cadence_reward_buffer += 2.0

                    drops_to_remove.append(drop)

        for drop in drops_to_remove:

            if drop in drops:
                drops.remove(drop)

    # --------------------------------------------------------
    # ROUND COMPLETE
    # --------------------------------------------------------

    if (
        zombies_spawned >= zombies_to_spawn
        and
        len(zombies) == 0
        and
        not round_complete
        and
        not game_over
    ):

        # Area 5 ends with a boss fight.
        if (
            area_number == 5
            and
            not boss_defeated
        ):

            if not boss_spawned:

                create_boss()

                boss_spawned = True

                boss_intro_timer = (
                    boss_intro_duration
                )

        else:

            round_complete = True
            exit_active = True
            cadence_reward_buffer += 10.0
            cadence_record_area_clear()
            cadence_save_official_brain()

    # --------------------------------------------------------
    # ENTER EXIT
    # --------------------------------------------------------

    if (
        exit_active
        and
        not game_over
        and
        distance(
            player_x,
            player_y,
            exit_x,
            exit_y
        ) < (
            player_radius +
            exit_radius
        )
    ):

        start_next_area()

    # --------------------------------------------------------
    # AUTONOMOUS TRAINING RESTART
    # --------------------------------------------------------

    if game_over:
        game_over_timer -= dt
        if game_over_timer <= 0:
            restart_game()

    # ========================================================
    # DRAW
    # ========================================================

    draw_world()

    # Exit
    if exit_active:
        draw_exit()

    # Drops
    for drop in drops:
        draw_drop(screen, drop)

    # Bullets
    for bullet in bullets:

        trail_x = (
            bullet["x"] -
            bullet["dx"] * 10
        )

        trail_y = (
            bullet["y"] -
            bullet["dy"] * 10
        )

        pygame.draw.line(
            screen,
            (255, 180, 70),
            (int(trail_x), int(trail_y)),
            (int(bullet["x"]), int(bullet["y"])),
            3
        )

        draw_soft_glow(
            screen,
            YELLOW,
            bullet["x"],
            bullet["y"],
            7,
            30
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (int(bullet["x"]), int(bullet["y"])),
            max(2, bullet["radius"] - 1)
        )

    # Flames
    for flame in flames:

        flame_color = random.choice(
            [
                YELLOW,
                ORANGE,
                FIRE_RED
            ]
        )

        pygame.draw.circle(
            screen,
            flame_color,
            (
                int(flame["x"]),
                int(flame["y"])
            ),
            int(flame["radius"])
        )

    # Zombies
    for zombie in zombies:
        draw_zombie(screen, zombie)

    # Boss health bar
    draw_boss_hud()

    # Cadence is the only character in the arena.
    if not transition_active and not game_over:
        draw_cadence(screen)

    # --------------------------------------------------------
    # HUD
    # --------------------------------------------------------

    area_name = area_names.get(
        area_number,
        f"INFECTED ZONE {area_number}"
    )

    area_text = font_small.render(
        f"AREA {area_number} // {area_name}",
        True,
        GREEN
    )

    screen.blit(
        area_text,
        (60, 52)
    )

    round_text = font_big.render(
        f"ROUND {round_number}",
        True,
        WHITE
    )

    screen.blit(
        round_text,
        (60, 78)
    )

    score_text = font_small.render(
        f"SCORE  {score}",
        True,
        YELLOW
    )

    screen.blit(
        score_text,
        (60, 118)
    )

    kills_text = font_small.render(
        f"KILLS  {round_kills}/{zombies_to_spawn}",
        True,
        WHITE
    )

    screen.blit(
        kills_text,
        (60, 144)
    )

    # --------------------------------------------------------
    # WEAPON HUD
    # --------------------------------------------------------

    if current_weapon == "RIFLE":

        weapon_text = "RIFLE  |  UNLIMITED"
        weapon_color = WHITE

    elif current_weapon == "MACHINE GUN":

        weapon_text = (
            f"MACHINE GUN  |  {special_ammo}"
        )

        weapon_color = BLUE

    else:

        weapon_text = (
            f"FLAMETHROWER  |  {special_ammo}"
        )

        weapon_color = ORANGE

    weapon_surface = font_medium.render(
        weapon_text,
        True,
        weapon_color
    )

    weapon_rect = weapon_surface.get_rect(
        topright=(
            WIDTH - 60,
            55
        )
    )

    screen.blit(
        weapon_surface,
        weapon_rect
    )

    # --------------------------------------------------------
    # HEALTH
    # --------------------------------------------------------

    health_text = font_small.render(
        f"CADENCE HEALTH {player_health}",
        True,
        WHITE
    )

    screen.blit(
        health_text,
        (
            60,
            HEIGHT - 105
        )
    )

    pygame.draw.rect(
        screen,
        DARK_RED,
        (
            60,
            HEIGHT - 75,
            220,
            18
        )
    )

    health_width = int(
        220 *
        player_health /
        max_player_health
    )

    pygame.draw.rect(
        screen,
        GREEN,
        (
            60,
            HEIGHT - 75,
            health_width,
            18
        )
    )

    # --------------------------------------------------------
    # CADENCE LEARNING HUD
    # --------------------------------------------------------

    draw_cadence_learning_hud()

    # --------------------------------------------------------
    # AREA CLEARED
    # --------------------------------------------------------

    if (
        round_complete
        and
        not transition_active
        and
        not game_over
    ):

        complete_text = font_big.render(
            "AREA CLEARED - ENTER EXIT",
            True,
            YELLOW
        )

        complete_rect = complete_text.get_rect(
            center=(
                WIDTH // 2,
                100
            )
        )

        screen.blit(
            complete_text,
            complete_rect
        )

    # --------------------------------------------------------
    # TRANSITION
    # --------------------------------------------------------

    if transition_active:

        overlay = pygame.Surface(
            (WIDTH, HEIGHT)
        )

        overlay.set_alpha(225)
        overlay.fill((5, 7, 6))

        screen.blit(
            overlay,
            (0, 0)
        )

        transition_title = font_huge.render(
            f"AREA {area_number}",
            True,
            GREEN
        )

        transition_name = font_big.render(
            area_name,
            True,
            WHITE
        )

        transition_round = font_small.render(
            (
                f"ROUND {round_number}"
                "  //  THREAT LEVEL INCREASED"
            ),
            True,
            YELLOW
        )

        title_rect = transition_title.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 - 55
            )
        )

        name_rect = transition_name.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 + 5
            )
        )

        round_rect = transition_round.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 + 55
            )
        )

        screen.blit(
            transition_title,
            title_rect
        )

        screen.blit(
            transition_name,
            name_rect
        )

        screen.blit(
            transition_round,
            round_rect
        )

    # --------------------------------------------------------
    # BOSS INTRO
    # --------------------------------------------------------

    if (
        boss_intro_timer > 0
        and
        not game_over
    ):

        boss_warning = font_huge.render(
            "BOSS INCOMING",
            True,
            RED
        )

        boss_name = font_big.render(
            "THE BRUTE",
            True,
            WHITE
        )

        warning_rect = boss_warning.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 - 30
            )
        )

        name_rect = boss_name.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 + 30
            )
        )

        screen.blit(
            boss_warning,
            warning_rect
        )

        screen.blit(
            boss_name,
            name_rect
        )

    # --------------------------------------------------------
    # DAMAGE FLASH
    # --------------------------------------------------------

    if player_hit_flash > 0:

        damage_overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        damage_overlay.fill(
            (180, 0, 0, 70)
        )

        screen.blit(
            damage_overlay,
            (0, 0)
        )

    # --------------------------------------------------------
    # GAME OVER
    # --------------------------------------------------------

    if game_over:

        game_over_overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        game_over_overlay.fill(
            (5, 0, 0, 220)
        )

        screen.blit(
            game_over_overlay,
            (0, 0)
        )

        died_text = font_huge.render(
            "CADENCE FAILED",
            True,
            RED
        )

        score_final_text = font_big.render(
            f"SCORE: {score}",
            True,
            WHITE
        )

        area_final_text = font_medium.render(
            f"AREA REACHED: {area_number}",
            True,
            WHITE
        )

        restart_text = font_small.render(
            "AUTO-RESTARTING // LEARNING SAVED",
            True,
            YELLOW
        )

        died_rect = died_text.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 - 90
            )
        )

        score_rect = score_final_text.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 - 20
            )
        )

        area_rect = area_final_text.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 + 25
            )
        )

        restart_rect = restart_text.get_rect(
            center=(
                WIDTH // 2,
                HEIGHT // 2 + 90
            )
        )

        screen.blit(
            died_text,
            died_rect
        )

        screen.blit(
            score_final_text,
            score_rect
        )

        screen.blit(
            area_final_text,
            area_rect
        )

        screen.blit(
            restart_text,
            restart_rect
        )

    # --------------------------------------------------------
    # STARTUP / TRAINING BANNER
    # --------------------------------------------------------

    if (
        startup_overlay_timer > 0
        and
        not game_over
    ):

        overlay = pygame.Surface(
            (
                WIDTH,
                HEIGHT
            ),
            pygame.SRCALPHA
        )

        overlay.fill(
            (
                2,
                6,
                10,
                185
            )
        )

        screen.blit(
            overlay,
            (
                0,
                0
            )
        )

        title = font_huge.render(
            "CADENCE // DEADZONE",
            True,
            BLUE
        )

        subtitle = font_big.render(
            "AUTONOMOUS TRAINING ACTIVE",
            True,
            WHITE
        )

        detail = font_medium.render(
            "Official Cadence Brain + persistent checkpoint learning",
            True,
            YELLOW
        )

        screen.blit(
            title,
            title.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 - 80
                )
            )
        )

        screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 + 5
                )
            )
        )

        screen.blit(
            detail,
            detail.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 + 70
                )
            )
        )

    pygame.display.flip()

# ============================================================
# QUIT
# ============================================================

cadence_save_official_brain()
cadence_save_training_stats()

pygame.mouse.set_visible(True)

pygame.quit()
sys.exit()