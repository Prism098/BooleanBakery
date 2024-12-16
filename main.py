import pygame
import sys
import random
import time

pygame.init()

# Window setup
WIDTH, HEIGHT = 1000, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Boolean Bakery")

# Fonts & Colors
FONT = pygame.font.SysFont("Arial", 24)
TITLE_FONT = pygame.font.SysFont("Arial", 36, bold=True)

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
ORANGE = (242, 159, 93)    # For the step boxes (example color)
LIGHT_ORANGE = (248, 200, 143)
GREEN = (135, 211, 124)
RED = (235, 106, 106)

# Load images (replace with your own)
BG_IMAGE = pygame.image.load("images/bg.jpg")
BG_IMAGE = pygame.transform.scale(BG_IMAGE, (WIDTH, HEIGHT))
BUTTON_IMAGE = pygame.image.load("images/button.png")
BUTTON_IMAGE = pygame.transform.scale(BUTTON_IMAGE, (120, 50))
TIMER_IMAGE = pygame.image.load("images/curtain.jpg")
TIMER_IMAGE = pygame.transform.scale(TIMER_IMAGE, (50, 50))

# Game constants
STEPS = [
    "Pak alle tools & ingrediënten",
    "Vul de bakblik met bakmix",
    "Mix de Ingrediënten",
    "Bak de cake"
]
CORRECT_ORDER = STEPS[:]  # The correct order is as defined above
TIME_LIMIT = 60  # 60 seconds to solve
POINTS_PER_CORRECT = 10

class Button:
    def __init__(self, x, y, text):
        self.image = BUTTON_IMAGE
        self.rect = self.image.get_rect(topleft=(x, y))
        self.text = text
    
    def draw(self, surf):
        surf.blit(self.image, self.rect)
        txt_surf = FONT.render(self.text, True, WHITE)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surf.blit(txt_surf, txt_rect)

    def clicked(self, pos):
        return self.rect.collidepoint(pos)

class DraggableStep:
    def __init__(self, text, x, y, width=300, height=50):
        self.text = text
        self.rect = pygame.Rect(x, y, width, height)
        self.dragging = False
        self.offset_x = 0
        self.offset_y = 0
        self.correct = False
        self.checked = False

    def draw(self, surf):
        color = ORANGE if not self.checked else (GREEN if self.correct else RED)
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        # Text centered in rect
        txt_surf = FONT.render(self.text, True, BLACK)
        txt_rect = txt_surf.get_rect(center=self.rect.center)
        surf.blit(txt_surf, txt_rect)

        # If checked, draw a ✓ or ✗
        if self.checked:
            symbol = "✓" if self.correct else "✗"
            sym_color = WHITE
            sym_surf = FONT.render(symbol, True, sym_color)
            sym_rect = sym_surf.get_rect(midleft=(self.rect.right + 10, self.rect.centery))
            surf.blit(sym_surf, sym_rect)

class Slot:
    def __init__(self, x, y, width=300, height=50, index=1):
        self.rect = pygame.Rect(x, y, width, height)
        self.filled_by = None
        self.index = index

    def draw(self, surf):
        pygame.draw.rect(surf, LIGHT_ORANGE, self.rect, border_radius=10)
        # Draw slot number
        num_surf = FONT.render(str(self.index), True, BLACK)
        num_rect = num_surf.get_rect(center=(self.rect.left - 20, self.rect.centery))
        surf.blit(num_surf, num_rect)

def main():
    # Shuffle steps on the left side
    puzzle_steps = STEPS[:]
    random.shuffle(puzzle_steps)

    # Create draggable steps
    # Left column: steps at x=100, y starting at 150
    step_y = 150
    draggable_steps = []
    for step in puzzle_steps:
        ds = DraggableStep(step, 100, step_y)
        draggable_steps.append(ds)
        step_y += 70

    # Create slots on the right side
    slot_start_y = 150
    slots = []
    for i in range(len(CORRECT_ORDER)):
        s = Slot(WIDTH - 400, slot_start_y, index=i+1)
        slots.append(s)
        slot_start_y += 70

    check_button = Button(WIDTH - 200, HEIGHT - 80, "Check!")
    start_time = time.time()
    solved = False
    score = 0

    running = True
    dragged_step = None

    while running:
        dt = pygame.time.Clock().tick(60) / 1000.0
        # Time left
        elapsed = time.time() - start_time
        time_left = TIME_LIMIT - elapsed
        if time_left <= 0 and not solved:
            # Time's up, force check
            # Mark all unverified steps as incorrect
            for slot in slots:
                if slot.filled_by:
                    slot.filled_by.checked = True
                    slot.filled_by.correct = (slot.filled_by.text == CORRECT_ORDER[slot.index-1])
            # Calculate score (no time bonus if timed out)
            score = sum(POINTS_PER_CORRECT for slot in slots if slot.filled_by and slot.filled_by.correct)
            solved = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                # Start dragging a step if clicked
                if not solved:
                    for ds in draggable_steps:
                        if ds.rect.collidepoint(pos):
                            dragged_step = ds
                            ds.dragging = True
                            ds.offset_x = ds.rect.x - pos[0]
                            ds.offset_y = ds.rect.y - pos[1]
                            break
                # Check button
                if check_button.clicked(pos) and not solved:
                    # Evaluate correctness
                    for slot in slots:
                        if slot.filled_by:
                            slot.filled_by.checked = True
                            correct_text = CORRECT_ORDER[slot.index-1]
                            slot.filled_by.correct = (slot.filled_by.text == correct_text)
                    # Calculate score: correct steps * POINTS_PER_CORRECT + time bonus
                    correct_count = sum(1 for s in slots if s.filled_by and s.filled_by.correct)
                    score = correct_count * POINTS_PER_CORRECT
                    if correct_count == len(CORRECT_ORDER):
                        # All correct, add time bonus
                        score += int(time_left)
                    solved = True

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragged_step:
                    # Snap to slot if overlapping
                    placed = False
                    for slot in slots:
                        if slot.rect.colliderect(dragged_step.rect):
                            # If slot empty, place here
                            if slot.filled_by is None:
                                slot.filled_by = dragged_step
                                dragged_step.rect.topleft = slot.rect.topleft
                                placed = True
                            else:
                                # Slot filled, do nothing or swap
                                pass
                    if not placed:
                        # Return to left area if not placed in slot
                        # (Alternatively, leave it where released)
                        pass
                    dragged_step.dragging = False
                    dragged_step = None

            elif event.type == pygame.MOUSEMOTION:
                if dragged_step and dragged_step.dragging:
                    mx, my = event.pos
                    dragged_step.rect.x = mx + dragged_step.offset_x
                    dragged_step.rect.y = my + dragged_step.offset_y

        # Draw everything
        SCREEN.blit(BG_IMAGE, (0, 0))

        # Title
        title_surf = TITLE_FONT.render("Boolean Bakery", True, WHITE)
        SCREEN.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 50))

        # Instructions (if not solved)
        if not solved:
            instr_surf = FONT.render("Sleep de stappen in de juiste volgorde en klik op 'Check!'", True, WHITE)
            SCREEN.blit(instr_surf, (WIDTH//2 - instr_surf.get_width()//2, 100))

        # Draw steps
        for ds in draggable_steps:
            ds.draw(SCREEN)

        # Draw slots
        for slot in slots:
            slot.draw(SCREEN)

        # Draw button
        if not solved:
            check_button.draw(SCREEN)

        # Draw timer (top right)
        SCREEN.blit(TIMER_IMAGE, (WIDTH - 100, 20))
        time_surf = FONT.render(str(int(time_left)) if time_left > 0 else "0", True, BLACK)
        SCREEN.blit(time_surf, (WIDTH - 60, 30))

        # If solved, show score feedback
        if solved:
            result_surf = FONT.render(f"Score: {score}", True, BLACK)
            SCREEN.blit(result_surf, (WIDTH//2 - result_surf.get_width()//2, HEIGHT - 100))

            # Optional: show a message depending on correctness
            correct_count = sum(1 for s in slots if s.filled_by and s.filled_by.correct)
            if correct_count == len(CORRECT_ORDER):
                msg = "Goed gedaan! Alle stappen zijn correct!"
            else:
                msg = "Niet alle stappen zijn correct, probeer het opnieuw!"
            msg_surf = FONT.render(msg, True, BLACK)
            SCREEN.blit(msg_surf, (WIDTH//2 - msg_surf.get_width()//2, HEIGHT - 140))

        pygame.display.flip()

if __name__ == "__main__":
    main()
