from graphics import *
import random

PAD = 10
WIDTH = 600
HEIGHT = 75
TEXT_HEIGHT = 10
TEXT_START = 52
UPDATE_RATE = 5
TEXT_OFFSET = Point(PAD + 45, PAD + 10)
BAR_OFFSET = Point(PAD, 30)
BAR_SIZE = Point(500, 40)
ONE_GRAPH_SIZE = Point(PAD + BAR_SIZE.getX() + PAD, BAR_OFFSET.getY() + BAR_SIZE.getY() + PAD)
CATEGORIES = [("cpu0", "0"), ("cpu1", "1"), ("cpu2", "2"), ("cpu3", "3")]
CATEGORY_NAMES = [x[0] for x in CATEGORIES]

class Bar:
  def __init__(self, name, bar_size, color, text_width):
    self.name = name
    self.bar_size = bar_size
    self.color = color
    self.text_width = text_width

class Graph:
  def __init__(self, category, label):
    super().__init__()
    self.category = category
    self.label = label

  def modulate(self, usages):
    if not self.category in usages:
      return
    usage = usages[self.category]
    if usage:
      for bar in self.bars:
        value = usage.get(bar.name)
        if value is not None:
          bar.bar_size = value

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
    # possible fonts are: 'helvetica', 'arial', 'courier', 'times roman'
    t.setFace("helvetica")
    t.draw(window)
    return t

  def draw_text(self, window, pos):
    x = pos.getX()
    drawn = []
    cpu = Bar(self.label, 1, "black", 1)
    drawn.append(self.draw_word(cpu, window, x, pos.getY()))
    x += 72
    for bar in self.bars:
      drawn.append(self.draw_word(bar, window, x, pos.getY()))
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
    total_size = sum([bar.bar_size for bar in self.bars])
    if total_size < 1:
      return []
    x = left
    drawn = []
    area.setFill("black")
    area.draw(window)
    drawn.append(area)
    for bar in self.bars:
      fraction = bar.bar_size / total_size
      next_x = x + (right - left) * fraction
      r = Rectangle(Point(x, top), Point(next_x, bottom))
      r.setFill(bar.color)
      r.setOutline(bar.color)
      r.draw(window)
      drawn.append(r)
      x = next_x
    drawn.extend(self.draw_ticks(window, self.get_tick_area(area)))
    return drawn

  def draw(self, window, position):
    text_pos = position.plus(TEXT_OFFSET)
    bar_pos = position.plus(BAR_OFFSET)
    bar_area = Rectangle(bar_pos, bar_pos.plus(BAR_SIZE))
    drawn = self.draw_text(window, text_pos)
    drawn.extend(self.draw_bars(window, bar_area))
    return drawn
  
class CpuGraph(Graph):
  def __init__(self, category):
    super().__init__(category[0], "CPU " + str(category[1]) + " Usage:")
    self.bars = []
    self.bars.append(Bar("user", 0, color_rgb(0, 0, 255), 35))
    self.bars.append(Bar("sys", 0, color_rgb(255, 0, 0), 28))
    self.bars.append(Bar("intr", 0, color_rgb(255, 255, 0), 30))
    self.bars.append(Bar("gfxf", 0, color_rgb(0, 255, 255), 33))
    self.bars.append(Bar("gfxc", 0, color_rgb(255, 0, 255), 34))
    self.bars.append(Bar("idle", 0, color_rgb(0, 255, 0), 30))

class Graphs:
  def __init__(self, graphs):
    self.all_graphs = graphs
  
  def size(self):
    return len(self.all_graphs)

  def modulate(self, usage):
    for graph in self.all_graphs:
      graph.modulate(usage)

  def draw(self, window):
    position = Point(0, 0)
    drawn = []
    for graph in self.all_graphs:
      drawn.extend(graph.draw(window, position))
      position = position.plus(Point(0, ONE_GRAPH_SIZE.getY()))
    return drawn

graphs = Graphs([CpuGraph(x) for x in CATEGORIES])

def draw(window):
  drawn = graphs.draw(window)
  update(UPDATE_RATE)
  for d in drawn:
    d.undraw()

def get_total_size():
  return Point(ONE_GRAPH_SIZE.getX(), graphs.size() * ONE_GRAPH_SIZE.getY())

def get_background():
  back = Rectangle(Point(0, 0), get_total_size())
  back.setFill("gray")
  return back

def get_cpu_usages():
  """Returns a dictionary of dictionaries"""
  usages = {}
  with open("/proc/stat", "r") as f:
    for line in f.readlines():
      tokens = line.split()
      if len(tokens) > 0 and tokens[0] in CATEGORY_NAMES:
        usages[tokens[0]] = {
          "user": int(tokens[1]),
          "sys": int(tokens[3]),
          "idle": int(tokens[4]),
          "intr": int(tokens[6]) + int(tokens[7])}
  return usages

prev_usages = None
def get_cpu_usages_diff():
  usages = get_cpu_usages()
  diff = {}
  global prev_usages
  if not prev_usages:
    prev_usages = usages
    return diff
  
  for category, usage in usages.items():
    if category in prev_usages:
      prev_usage = prev_usages[category]
      if prev_usage:
        for k, v in usage.items():
          if not category in diff:
            diff[category] = {}
          diff[category][k] = v - prev_usage[k]

  prev_usages = usages
  return diff

def main():
  win = GraphWin("gr_osview", get_total_size().getX(), get_total_size().getY(), autoflush=False)
  get_background().draw(win)
  while True:
    graphs.modulate(get_cpu_usages_diff())
    draw(win)
  win.close()

main()
