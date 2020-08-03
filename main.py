from graphics import *
import random

PAD = 10
WIDTH = 600
HEIGHT = 75
TEXT_HEIGHT = 10
TEXT_START = 52
UPDATE_RATE = 5

class Bar:
  def __init__(self, name, size, color, text_width):
    self.name = name
    self.size = size
    self.color = color
    self.text_width = text_width
  
  def modulate(self):
    self.size += random.randrange(-100, 100) / 50.0
    if self.size < 0.1:
      self.size = 0.1
    if self.size > 30172872:
      self.size = 30172872

class Graph:
  def __init__(self):
    self.bars = []
    self.bars.append(Bar("user", 0, color_rgb(0, 0, 255), 35))
    self.bars.append(Bar("sys", 0, color_rgb(255, 0, 0), 28))
    self.bars.append(Bar("intr", 0, color_rgb(255, 255, 0), 30))
    self.bars.append(Bar("gfxf", 0, color_rgb(0, 255, 255), 33))
    self.bars.append(Bar("gfxc", 0, color_rgb(255, 0, 255), 34))
    self.bars.append(Bar("idle", 0, color_rgb(0, 255, 0), 30))
  
  def modulate(self, usages):
    for bar in self.bars:
      # bar.modulate()
      value = usages.get(bar.name)
      if value:
        bar.size = value

  def shrink_area(self, area):
    x = 1
    y = 1
    bottom = 3
    return Rectangle(
        Point(area.getP1().getX() + x, area.getP1().getY() + y),
        Point(area.getP2().getX() - x, area.getP2().getY() - bottom))
  
  def draw_word(self, bar, window, x, y):
    t = Text(Point(x, y), bar.name)
    t.setFill(bar.color)
    t.setStyle("italic")
    # 'helvetica','arial','courier','times roman'
    t.setFace("helvetica")
    t.draw(window)
    return t

  def draw_text(self, window, x, y):
    drawn = []
    cpu = Bar("CPU Usage:", 1, "black", 1)
    drawn.append(self.draw_word(cpu, window, x, y))
    x += 65
    for bar in self.bars:
      drawn.append(self.draw_word(bar, window, x, y))
      x += bar.text_width
    return drawn

  def get_tick_area(self, area):
    height = 2
    return Rectangle(
      Point(area.getP1().getX() + 1, area.getP2().getY() - height),
      Point(area.getP2().getX() - 1, area.getP2().getY()))

  def draw_ticks(self, window, area):
    spacing = (area.getP2().getX() - area.getP1().getX()) / 10.0
    x = area.getP1().getX()
    drawn = []
    for i in range(11):
      l = Line(Point(x, area.getP1().getY()), Point(x, area.getP2().getY()))
      l.setFill("white")
      drawn.append(l.draw(window))
      x += spacing
    return drawn

  def draw_bars(self, window, area):
    area2 = self.shrink_area(area)
    left = area2.getP1().getX()
    right = area2.getP2().getX()
    top = area2.getP2().getY()
    bottom = area2.getP1().getY()
    total_size = sum([bar.size for bar in self.bars])
    if total_size < 1:
      return []
    x = left
    drawn = []
    area.setFill("black")
    area.draw(window)
    drawn.append(area)
    for bar in self.bars:
      fraction = bar.size / total_size
      next_x = x + (right - left) * fraction
      r = Rectangle(Point(x, top), Point(next_x, bottom))
      r.setFill(bar.color)
      r.setOutline(bar.color)
      r.draw(window)
      drawn.append(r)
      x = next_x
    drawn.extend(self.draw_ticks(window, self.get_tick_area(area)))
    return drawn

graph = Graph()

def get_text_pos():
  return Point(TEXT_START, PAD + TEXT_HEIGHT / 2)

def get_graph_area():
  return Rectangle(Point(PAD, 2 * PAD + TEXT_HEIGHT), Point(WIDTH - PAD, HEIGHT - PAD))

def draw(window):
  drawn = graph.draw_text(window, get_text_pos().getX(), get_text_pos().getY())
  drawn.extend(graph.draw_bars(window, get_graph_area()))
  update(UPDATE_RATE)
  for d in drawn:
    d.undraw()

def get_background():
  back = Rectangle(Point(0, 0), Point(WIDTH, HEIGHT))
  back.setFill("gray")
  return back

def get_cpu_usage():
  with open("/proc/stat", "r") as f:
    cpu_line = f.readline()
    tokens = cpu_line.split()
    if tokens[0] != 'cpu':
      print("Failed to parse /proc/stat: " + cpu_line)
  return {
    "user": int(tokens[1]),
    "sys": int(tokens[3]),
    "idle": int(tokens[4]),
    "intr": int(tokens[6]) + int(tokens[7])}

prev_usage = None
def get_cpu_usage_diff():
  usage = get_cpu_usage()
  diff = {}
  global prev_usage
  if not prev_usage:
    prev_usage = usage
    return diff
  for k, v in usage.items():
    if prev_usage.get(k):
      diff[k] = v - prev_usage.get(k)
  prev_usage = usage
  return diff

def main():
  win = GraphWin("gr_osview", WIDTH, HEIGHT, autoflush=False)
  get_background().draw(win)
  while True:
    graph.modulate(get_cpu_usage_diff())
    draw(win)
  win.close()

main()
