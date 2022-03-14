import pygame
import os
import serial
import serial.tools.list_ports
from dvbcdr.utils.pygame_ext import PygCdrScene, PygCdrText, PygCdrInputBox, PygCdrSurface

os.chdir(os.path.dirname(os.path.abspath(__file__)))
pygame.init()

window = pygame.display.set_mode((600, 400), pygame.HWSURFACE | pygame.DOUBLEBUF)
pygame.display.set_caption("Robot PID Tester")

clock = pygame.time.Clock()
scene = PygCdrScene(window)

serial_port: serial.Serial = None
running_test = False
received_data = ""
graph_data = []
graph_needs_update = True


def run_test():
    global running_test, graph_data, graph_needs_update, serial_port, scene

    if running_test:
        return

    if serial_port is None or not serial_port.is_open():
        disconnect()

    running_test = True
    graph_data = []
    graph_needs_update = True

    try:
        kp = float(scene["p_input"].text)
        ki = float(scene["i_input"].text)
        kd = float(scene["d_input"].text)
    except ValueError:
        set_status("Invalid input!")
        return

    set_status("Running test...")
    serial_port.write(bytes("run/" + str(kp) + " " + str(ki) + " " + str(kd) + "\n", "ascii"))


def try_connect():
    global serial_port

    if serial_port is None:
        paths = [x.device for x in serial.tools.list_ports.comports()]
        for port_path in paths:
            try:
                port = serial.Serial(port_path, baudrate=115200, timeout=0)

                serial_port = port

                scene.hide_group("disconnected")
                scene.show_group("connected")
                set_status("")

                break
            except serial.SerialException:
                continue

    if serial_port is None:
        scene["disconnected_text"].render_text("Could not connect!")


def disconnect():
    global serial_port

    if serial_port is not None:
        if serial_port.is_open():
            serial_port.close()
        serial_port = None

    scene.hide_group("connected")
    scene.show_group("disconnected")
    scene["disconnected_text"].render_text("Disconnected")


def draw_graph(surface: pygame.Surface):
    global graph_data, graph_needs_update

    if not graph_needs_update:
        return

    surface.fill((255, 255, 255))

    pygame.draw.line(surface, (0, 0, 0), (30, 0), (30, 300))
    pygame.draw.line(surface, (0, 0, 0), (30, 300), (530, 300))

    font = pygame.font.SysFont("Arial", 12)
    surface.blit(font.render("0", True, (0, 0, 0)), (20, 305))
    surface.blit(font.render("5s", True, (0, 0, 0)), (515, 305))

    count = len(graph_data)
    if count > 0:
        max_val = max(graph_data)
        surface.blit(font.render(str(max_val), True, (0, 0, 0)), (5, 0))

        # 5s = 500px = all data inside the list
        pygame.draw.lines(surface, "blue", False, points=[(30 + 500 * i / (count - 1), 300 - (300 * x / max_val)) for i, x in enumerate(graph_data)])

    graph_needs_update = False


def set_status(text: str):
    scene["status_text"].render_text(text)


# WINDOW SETUP
scene.add_element("p_legend", PygCdrText("P:", pos=(10, 10), font_size=14))
scene.add_element("p_input", PygCdrInputBox("1", pos=(30, 10), size=(50, 20), font_size=14))

scene.add_element("i_legend", PygCdrText("I:", pos=(100, 10), font_size=14))
scene.add_element("i_input", PygCdrInputBox("0", pos=(120, 10), size=(50, 20), font_size=14))

scene.add_element("d_legend", PygCdrText("D:", pos=(190, 10), font_size=14))
scene.add_element("d_input", PygCdrInputBox("0", pos=(210, 10), size=(50, 20), font_size=14))

scene.add_element("run_button", PygCdrText("Run test", pos=(300, 10), font_size=14, bg_color=(150, 150, 150), size=(80, 20), onclick=run_test))
scene.add_element("status_text", PygCdrText("", pos=(400, 10), font_size=14))

scene.add_to_group("connected", "p_legend", "p_input", "i_legend", "i_input", "d_legend", "d_input", "run_button", "status_text")

scene.add_element("disconnected_text", PygCdrText("Disconnected", pos=(10, 10), font_size=14))
scene.add_element("connect_button", PygCdrText("Connect", pos=(200, 10), font_size=14, bg_color=(150, 150, 150), size=(80, 20), onclick=try_connect))

scene.add_to_group("disconnected", "disconnected_text", "connect_button")

scene.add_element("graph", PygCdrSurface(pos=(20, 60), size=(530, 320), draw=draw_graph))
scene.add_to_group("connected", "graph")


scene.hide_group("connected")

# WINDOW LOOP
while True:
    if scene.handle_events():
        break

    # update logic
    if running_test and serial_port is not None and serial_port.is_open():
        try:
            data = serial_port.readline().decode("ascii").strip()
            if data != "":
                received_data += data
                if received_data.endswith("/done\n"):
                    received_data = received_data[received_data.index("data/") + 5:received_data.index("/done\n")]
                    graph_data = [int(x) for x in received_data.split(" ")]
                    graph_needs_update = True
                    running_test = False
                    set_status("Test finished!")
        except serial.SerialException:
            disconnect()

    # draws the new scene
    scene.show()

    clock.tick(24)

pygame.quit()
