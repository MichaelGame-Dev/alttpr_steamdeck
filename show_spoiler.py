#!/usr/bin/env python3
"""Show a full-screen QR code linking to a seed's alttpr.com page (which has its spoiler).

Closes on any controller button, key, click, or after a timeout.
"""
import argparse
import json
import sys
from pathlib import Path

import pygame
import segno

BG = (16, 24, 32)
FG = (235, 235, 235)
ACCENT = (240, 200, 80)


def draw_qr(surface, url, center, max_size):
    qr = segno.make(url, error="m")
    matrix = list(qr.matrix_iter(border=4))
    cell = max(1, max_size // len(matrix))
    size = cell * len(matrix)
    left, top = center[0] - size // 2, center[1] - size // 2
    pygame.draw.rect(surface, (255, 255, 255), (left, top, size, size))
    for y, row in enumerate(matrix):
        for x, dark in enumerate(row):
            if dark:
                pygame.draw.rect(surface, (0, 0, 0), (left + x * cell, top + y * cell, cell, cell))
    return top + size


def render(screen, meta):
    w, h = screen.get_size()
    screen.fill(BG)
    big = pygame.font.Font(None, h // 14)
    small = pygame.font.Font(None, h // 26)

    def text(font, s, y, color=FG):
        surf = font.render(s, True, color)
        screen.blit(surf, (w // 2 - surf.get_width() // 2, y))
        return y + surf.get_height() + h // 80

    y = text(big, "Spoiler - scan with your phone", h // 20, ACCENT)
    qr_bottom = draw_qr(screen, meta["url"], (w // 2, y + h * 3 // 10), h * 6 // 10)
    y = text(small, meta["url"], qr_bottom + h // 40)
    y = text(small, "File select code: " + " / ".join(meta["code"]), y)
    text(small, f"Preset: {meta['preset']}    Generated: {meta['generated']}", y)
    text(small, "Press any button to close", h - h // 14, (150, 150, 150))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("meta", type=Path, help="Seed metadata .json written by generate_seed.py")
    parser.add_argument("--timeout", type=int, default=300, help="Seconds before closing automatically")
    parser.add_argument("--screenshot", type=Path, help="Render once to this PNG and exit (for testing)")
    args = parser.parse_args()

    meta = json.loads(args.meta.read_text())
    # Build the permalink from the hash so seeds saved with the old /h/ URL format still work.
    meta["url"] = f"https://alttpr.com/en/h/{meta['hash']}"

    pygame.init()
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

    if args.screenshot:
        screen = pygame.display.set_mode((1920, 1080))
        render(screen, meta)
        pygame.image.save(screen, str(args.screenshot))
        return 0

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("ALttPR Spoiler")
    pygame.mouse.set_visible(False)
    render(screen, meta)
    pygame.display.flip()

    clock = pygame.time.Clock()
    elapsed = 0
    # Ignore input briefly so the button press that launched us doesn't close the screen.
    grace_ms = 750
    while elapsed < args.timeout * 1000:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 0
            if event.type == pygame.JOYDEVICEADDED:
                joysticks.append(pygame.joystick.Joystick(event.device_index))
            if elapsed > grace_ms and event.type in (
                pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN, pygame.CONTROLLERBUTTONDOWN
            ):
                return 0
            if event.type == pygame.VIDEOEXPOSE:
                render(screen, meta)
                pygame.display.flip()
        elapsed += clock.tick(30)
    return 0


if __name__ == "__main__":
    sys.exit(main())
