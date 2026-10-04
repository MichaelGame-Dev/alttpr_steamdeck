#!/usr/bin/env python3
"""Full-screen, controller-driven spoiler viewer for the TV.

Areas are listed on the left; an area's items stay hidden until you press A on it.
D-pad/stick: move   A: reveal/open   B: back (quits from the area list)   Start/Esc: quit
"""
import argparse
import json
import sys
from pathlib import Path

import pygame
from pygame._sdl2 import controller as sdl_controller

from spoiler_data import sections

BG = (16, 24, 32)
PANEL = (26, 36, 48)
FG = (235, 235, 235)
MUTED = (140, 150, 160)
ACCENT = (240, 200, 80)
SELECT = (60, 90, 130)

REPEAT_DELAY_MS, REPEAT_MS = 350, 70
GRACE_MS = 500
STICK_DEADZONE = 16000


class Viewer:
    def __init__(self, screen, meta, secs):
        self.screen, self.meta, self.secs = screen, meta, secs
        self.sel = 0
        self.focus = "list"
        self.revealed = set()
        self.scroll = 0
        w, h = screen.get_size()
        self.w, self.h = w, h
        self.title_font = pygame.font.Font(None, h // 16)
        self.font = pygame.font.Font(None, h // 28)
        self.small = pygame.font.Font(None, h // 36)
        self.line_h = self.font.get_linesize() + h // 200
        self.top = h // 6
        self.bottom = h - h // 12
        self.rows_per_page = (self.bottom - self.top) // self.line_h

    # --- input ---
    def act(self, action):
        """Apply one action. Returns False when the viewer should close."""
        rows = self.secs[self.sel][1]
        max_scroll = max(0, len(rows) - self.rows_per_page)
        if action == "quit":
            return False
        if self.focus == "list":
            if action == "up":
                self.sel = (self.sel - 1) % len(self.secs)
            elif action == "down":
                self.sel = (self.sel + 1) % len(self.secs)
            elif action in ("a", "right"):
                self.revealed.add(self.sel)
                self.focus, self.scroll = "items", 0
            elif action == "b":
                return False
        else:
            if action == "up":
                self.scroll = max(0, self.scroll - 1)
            elif action == "down":
                self.scroll = min(max_scroll, self.scroll + 1)
            elif action == "pageup":
                self.scroll = max(0, self.scroll - self.rows_per_page)
            elif action == "pagedown":
                self.scroll = min(max_scroll, self.scroll + self.rows_per_page)
            elif action in ("b", "left"):
                self.focus = "list"
        return True

    # --- drawing ---
    def fit(self, font, text, width):
        if font.size(text)[0] <= width:
            return text
        while text and font.size(text + "…")[0] > width:
            text = text[:-1]
        return text + "…"

    def blit(self, font, text, x, y, color, width=None, right=False):
        if width:
            text = self.fit(font, text, width)
        surf = font.render(text, True, color)
        self.screen.blit(surf, (x + width - surf.get_width() if right else x, y))

    def draw(self):
        s, w, h = self.screen, self.w, self.h
        s.fill(BG)
        pad = w // 60
        self.blit(self.title_font, "Spoiler", pad, h // 30, ACCENT)
        code = " / ".join(self.meta.get("code", []))
        self.blit(self.small, f"Seed {self.meta.get('hash', '')}   ·   {self.meta.get('preset', '')}   ·   File select: {code}",
                  pad, h // 30 + self.title_font.get_linesize(), MUTED, w - 2 * pad)

        # Area list
        list_w = w * 3 // 10
        first = max(0, min(self.sel - self.rows_per_page // 2, len(self.secs) - self.rows_per_page))
        for i, (title, _) in enumerate(self.secs[first:first + self.rows_per_page], start=first):
            y = self.top + (i - first) * self.line_h
            if i == self.sel:
                color = SELECT if self.focus == "list" else PANEL
                pygame.draw.rect(s, color, (pad // 2, y - 2, list_w - pad, self.line_h), border_radius=6)
            mark = "• " if i in self.revealed else "   "
            self.blit(self.font, mark + title, pad, y, FG if i == self.sel else MUTED, list_w - 2 * pad)

        # Items panel
        px = list_w
        pw = w - px - pad
        pygame.draw.rect(s, PANEL, (px, self.top - pad // 2, pw, self.bottom - self.top + pad), border_radius=10)
        title, rows = self.secs[self.sel]
        inner_x, inner_w = px + pad, pw - 2 * pad
        if self.sel not in self.revealed:
            self.blit(self.font, f"Press A to reveal: {title}", inner_x, self.top + self.line_h, MUTED, inner_w)
        else:
            left_w = inner_w * 3 // 5
            for j, (left, right) in enumerate(rows[self.scroll:self.scroll + self.rows_per_page]):
                y = self.top + j * self.line_h
                if right:
                    self.blit(self.font, left, inner_x, y, FG, left_w - pad)
                    self.blit(self.font, right, inner_x + left_w, y, ACCENT, inner_w - left_w, right=True)
                else:
                    self.blit(self.font, left, inner_x, y, MUTED)
            if len(rows) > self.rows_per_page:
                last = min(len(rows), self.scroll + self.rows_per_page)
                self.blit(self.small, f"{self.scroll + 1}-{last} of {len(rows)}", inner_x, self.bottom, MUTED,
                          inner_w, right=True)

        hint = ("D-pad: choose area    A: reveal    B: quit" if self.focus == "list"
                else "D-pad: scroll    L/R shoulder: page    B: back to areas")
        self.blit(self.small, hint, pad, h - h // 20, MUTED)


BUTTONS = {
    pygame.CONTROLLER_BUTTON_DPAD_UP: "up", pygame.CONTROLLER_BUTTON_DPAD_DOWN: "down",
    pygame.CONTROLLER_BUTTON_DPAD_LEFT: "left", pygame.CONTROLLER_BUTTON_DPAD_RIGHT: "right",
    pygame.CONTROLLER_BUTTON_A: "a", pygame.CONTROLLER_BUTTON_B: "b",
    pygame.CONTROLLER_BUTTON_LEFTSHOULDER: "pageup", pygame.CONTROLLER_BUTTON_RIGHTSHOULDER: "pagedown",
    pygame.CONTROLLER_BUTTON_START: "quit",
}
KEYS = {
    pygame.K_UP: "up", pygame.K_DOWN: "down", pygame.K_LEFT: "left", pygame.K_RIGHT: "right",
    pygame.K_RETURN: "a", pygame.K_SPACE: "a", pygame.K_BACKSPACE: "b",
    pygame.K_PAGEUP: "pageup", pygame.K_PAGEDOWN: "pagedown", pygame.K_ESCAPE: "quit", pygame.K_q: "quit",
}
REPEATABLE = {"up", "down", "left", "right", "pageup", "pagedown"}


def open_controllers(controllers):
    sdl_controller.init()
    for i in range(sdl_controller.get_count()):
        if sdl_controller.is_controller(i):
            controllers.append(sdl_controller.Controller(i))


def run(viewer, timeout_s):
    controllers = []
    open_controllers(controllers)
    clock = pygame.time.Clock()
    held, next_repeat, stick = None, 0, None
    idle = 0
    dirty = True
    start = pygame.time.get_ticks()
    while idle < timeout_s * 1000:
        now = pygame.time.get_ticks()
        actions = []
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.CONTROLLERDEVICEADDED:
                controllers.append(sdl_controller.Controller(event.device_index))
            elif event.type == pygame.CONTROLLERBUTTONDOWN and event.button in BUTTONS:
                actions.append(BUTTONS[event.button])
                held, next_repeat = BUTTONS[event.button], now + REPEAT_DELAY_MS
            elif event.type == pygame.CONTROLLERBUTTONUP and BUTTONS.get(event.button) == held:
                held = None
            elif event.type == pygame.CONTROLLERAXISMOTION and event.axis == pygame.CONTROLLER_AXIS_LEFTY:
                new = "up" if event.value < -STICK_DEADZONE else "down" if event.value > STICK_DEADZONE else None
                if new != stick:
                    stick = new
                    if new:
                        actions.append(new)
                        held, next_repeat = new, now + REPEAT_DELAY_MS
                    elif held in ("up", "down"):
                        held = None
            elif event.type == pygame.KEYDOWN and event.key in KEYS:
                actions.append(KEYS[event.key])
                held, next_repeat = KEYS[event.key], now + REPEAT_DELAY_MS
            elif event.type == pygame.KEYUP and KEYS.get(event.key) == held:
                held = None
            elif event.type in (pygame.VIDEOEXPOSE, pygame.WINDOWEXPOSED):
                dirty = True
        if held in REPEATABLE and now >= next_repeat:
            actions.append(held)
            next_repeat = now + REPEAT_MS
        if now < start + GRACE_MS:
            # Drop the button press that launched us from Steam, so it can't reveal an area.
            actions, held = [], None
        for a in actions:
            if not viewer.act(a):
                return
        if actions:
            idle, dirty = 0, True
        if dirty:
            viewer.draw()
            pygame.display.flip()
            dirty = False
        idle += clock.tick(60)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("meta", type=Path, help="Seed metadata .json written by generate_seed.py")
    parser.add_argument("--timeout", type=int, default=1800, help="Close after this many idle seconds")
    parser.add_argument("--screenshot", type=Path, help="Render to this PNG and exit (for testing)")
    parser.add_argument("--actions", default="", help="Comma-separated actions to apply before --screenshot")
    args = parser.parse_args()

    meta = json.loads(args.meta.read_text())
    spoiler_path = args.meta.with_name(args.meta.name.removesuffix(".json") + ".spoiler.json")
    secs = sections(json.loads(spoiler_path.read_text()))
    if not secs:
        print(f"No spoiler data in {spoiler_path}", file=sys.stderr)
        return 1

    pygame.init()
    if args.screenshot:
        viewer = Viewer(pygame.display.set_mode((1920, 1080)), meta, secs)
        for a in filter(None, args.actions.split(",")):
            viewer.act(a)
        viewer.draw()
        pygame.image.save(viewer.screen, str(args.screenshot))
        return 0

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("ALttPR Spoiler")
    pygame.mouse.set_visible(False)
    run(Viewer(screen, meta, secs), args.timeout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
