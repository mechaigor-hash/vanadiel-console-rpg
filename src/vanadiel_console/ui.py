from __future__ import annotations

import re
import shutil
import textwrap
from dataclasses import dataclass
from typing import Callable

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def visible_len(text: str) -> int:
    return len(ANSI_RE.sub("", text))


def terminal_width(min_width: int = 40, max_width: int = 96) -> int:
    width = shutil.get_terminal_size((64, 20)).columns
    return max(min_width, min(max_width, width))


def divider(char: str = "─", width: int | None = None) -> str:
    return char * (width or terminal_width())


def wrap_line(text: str, indent: str = "", subsequent: str | None = None, width: int | None = None) -> str:
    max_width = width or terminal_width()
    return textwrap.fill(text, width=max_width, initial_indent=indent, subsequent_indent=subsequent or indent)


@dataclass(frozen=True)
class MenuOption:
    key: str
    label: str
    action: Callable[[], None] | None = None
    target: str | None = None


@dataclass
class Screen:
    slug: str
    title: str
    options: list[MenuOption]
    body: Callable[[], None] | None = None


class Navigator:
    """Tiny text-GUI screen navigator with back/home/quit commands."""

    def __init__(self, screens: dict[str, Screen], start: str = "main") -> None:
        self.screens = screens
        self.current = start
        self.history: list[str] = []
        self.running = True

    def goto(self, slug: str) -> None:
        if slug not in self.screens:
            raise KeyError(f"Unknown screen: {slug}")
        self.history.append(self.current)
        self.current = slug

    def back(self) -> None:
        if self.history:
            self.current = self.history.pop()

    def home(self) -> None:
        self.current = "main"
        self.history.clear()

    def stop(self) -> None:
        self.running = False

    def breadcrumbs(self) -> str:
        names = [self.screens[slug].title for slug in [*self.history[-3:], self.current] if slug in self.screens]
        return f" {DIM}>{RESET} ".join(names)

    def render(self) -> None:
        screen = self.screens[self.current]
        width = terminal_width()
        print(f"\n{CYAN}{divider('═', width)}{RESET}")
        heading = f"{screen.title}  {self.breadcrumbs()}"
        print(wrap_line(heading, width=width))
        print(f"{CYAN}{divider('─', width)}{RESET}")
        if screen.body:
            screen.body()
            print(f"{CYAN}{divider('─', width)}{RESET}")
        for option in screen.options:
            label = wrap_line(option.label, indent=f"  {option.key}. ", subsequent="     ", width=width)
            print(label)
        print(wrap_line("b. Back    h. Home    q. Quit", indent="  ", subsequent="  ", width=width))

    def handle(self, raw: str) -> None:
        choice = raw.strip().lower()
        if choice == "b":
            self.back()
            return
        if choice == "h":
            self.home()
            return
        if choice == "q":
            self.stop()
            return
        screen = self.screens[self.current]
        for option in screen.options:
            if choice == option.key.lower():
                if option.target:
                    self.goto(option.target)
                if option.action:
                    option.action()
                return
        print(f"{RED}Unknown option: {raw}{RESET}")

    def run(self, clear: Callable[[], None] | None = None, header: Callable[[], None] | None = None, pause: Callable[[], None] | None = None) -> None:
        while self.running:
            if clear:
                clear()
            if header:
                header()
            self.render()
            self.handle(input("> "))
            if self.running and pause:
                pause()
