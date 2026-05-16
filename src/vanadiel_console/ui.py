from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

RESET = "\033[0m"
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"


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
        print(f"\n{CYAN}{'═' * 64}{RESET}")
        print(f"{BOLD}{screen.title}{RESET}  {DIM}{self.breadcrumbs()}{RESET}")
        print(f"{CYAN}{'─' * 64}{RESET}")
        if screen.body:
            screen.body()
            print(f"{CYAN}{'─' * 64}{RESET}")
        for option in screen.options:
            print(f"  {YELLOW}{option.key}.{RESET} {option.label}")
        print(f"  {YELLOW}b.{RESET} Back    {YELLOW}h.{RESET} Home    {YELLOW}q.{RESET} Quit")

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
