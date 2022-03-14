from dvbcdr.utils.pygame_ext import PygCdrScene, PygCdrObject, PygCdrText, PygCdrSlider, PygCdrSurface, PygCdrCheckbox
from dvbcdr.intercom import Intercom
from gui_utils import mouse_to_table, table_to_mouse

import lidar_renderer
import pygame
import os


os.chdir(os.path.dirname(os.path.abspath(__file__)))
pygame.init()

intercom = Intercom()
# intercom.wait_in_new_thread()

# CONSTANTS
irl_size = (3000, 2000)
table_size = (1200, 800)
margins = (120, 80)

robot_start_positions = [
    # (200, 250, 0),
    (2800, 950, 0),  # for lidar tests
    (200, 830, 0)
]


# PYGAME SETUP
window = pygame.display.set_mode((1200 + 2 * margins[0], 800 + 2 * margins[1]), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Table Visualizer")
pygame.display.set_icon(pygame.image.load("images/logo_ageofbots.png"))

table_image = pygame.transform.scale(pygame.image.load("images/table.png"), table_to_mouse((3000, 2000), table_size, irl_size))
robot_image = pygame.transform.scale(pygame.image.load("images/robot.png"), table_to_mouse((270, 220), table_size, irl_size))

running = True
clock = pygame.time.Clock()
scene = PygCdrScene(window)


# LOGIC UTILITIES
statuses = {}
statuses_key = {"cursor_position": "Cursor position"}


def set_status_part(key, value):
    if value is None:
        del statuses[key]
    else:
        statuses[key] = value


# LOGIC SETUP
# if True, the slider will not show the current rotation
# this value should be reset to False when a new position is set or when the requested rotation is reached
is_rotation_requested = False
debug_mode = False
selected_robot = 0
robot_count = 2
robot_positions = [*robot_start_positions]


def table_clicked():
    if not debug_mode:
        return

    # [*(tuple)] transforms a tuple into a list/array with the * (= deconstruct) operator
    # TODO: why not list(tuple)? the list constructor should correctly iterate the tuple
    intercom.publish("move_robot", [selected_robot, *mouse_to_table(pygame.mouse.get_pos(), table_size, irl_size, margins), -1])  # -1 is no forced rotation


def cycle_selected_robot():
    global selected_robot
    selected_robot = (selected_robot + 1) % robot_count

    scene.elements["change_robot"].render_text(f"Current robot: {selected_robot}")


def debug_mode_changed(new_mode):
    global debug_mode
    debug_mode = new_mode


def rotation_set(value):
    pass


last_lidar_messages = {}  # dict of array, one for each robot


def lidar_distances_received(message):
    global last_lidar_messages
    last_lidar_messages[message[0]] = message[1:]


intercom.subscribe("lidar_distances", lidar_distances_received)


def robot_position_received(message):
    robot_positions[message[0]] = tuple(message[1:])


intercom.subscribe("robot_position", robot_position_received)

# SCENE SETUP
status_text = scene.add_element("status_text", PygCdrText("", font_size=15, pos=(3, 3)))
scene.add_element("table", PygCdrObject(object=table_image, pos=(margins[0], margins[1]), size=table_size, cursor_data=("diamond", pygame.cursors.diamond),
                                        onhover=lambda: set_status_part("cursor_position", mouse_to_table(pygame.mouse.get_pos(), table_size, irl_size, margins)),
                                        onleave=lambda: set_status_part("cursor_position", None),
                                        onclick=table_clicked))
scene.add_element("rotation_text", PygCdrText("Rotation (0°):", font_size=15, pos=(3, 25)))
scene.add_element("rotation_slider", PygCdrSlider(0, 359, 1, 0, "white", "grey", "grey40", pos=(130, 25),
                                                  oninput=rotation_set))

for i in range(robot_count):
    scene.add_element(f"robot{i}_preview", PygCdrObject(object=robot_image, pos=table_to_mouse(robot_start_positions[i][0:2], table_size, irl_size, margins), size=robot_image.get_size(), anchor=(0.5, 0.5)))

scene.add_element("change_robot", PygCdrText("Current robot: 0", font_size=15, pos=(350, 10), size=(150, 30), cursor_data=("tri_left", pygame.cursors.tri_left),
                                             onclick=cycle_selected_robot, bg_color=(200, 200, 200)))

scene.add_element("lidar_display", PygCdrSurface(lidar_renderer.generate_draw_callback(robot_positions, last_lidar_messages, table_size, irl_size), size=table_size, pos=margins))

scene.add_element("debug_checkbox", PygCdrCheckbox("Controlled by debug?", size=(230, 18), checked=True, pos=(5, 45), onchange=debug_mode_changed))

# GAME LOOP
frame = 0
while True:
    if scene.handle_events():
        break

    status = ""
    for key, value in statuses.items():
        status += "{}: {}  ".format(statuses_key[key], value)
    status_text.render_text(status)

    if frame % 6 == 0:
        intercom.publish("debug_mode", int(debug_mode))

    # draws the new scene
    scene.show()

    frame += 1
    clock.tick(24)

pygame.quit()
