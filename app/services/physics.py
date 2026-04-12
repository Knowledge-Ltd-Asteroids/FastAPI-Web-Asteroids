import math
from typing import Dict, Tuple


def circle_collide(circle1: Dict, circle2: Dict) -> bool:
    x_dist = circle2["position"]["x"] - circle1["position"]["x"]
    y_dist = circle2["position"]["y"] - circle1["position"]["y"]
    
    distance = math.sqrt(x_dist ** 2 + y_dist ** 2)
    
    return distance <= circle1["radius"] + circle2["radius"]


def is_point_on_line_segment(x: float, y: float, begin: Dict, end: Dict) -> bool:
    return (
        x >= min(begin["x"], end["x"])
        and x <= max(begin["x"], end["x"])
        and y >= min(begin["y"], end["y"])
        and y <= max(begin["y"], end["y"])
    )


def circle_triangle_collision(circle: Dict, triangle: list) -> bool:
    for i in range(3):
        begin = triangle[i]
        end = triangle[(i + 1) % 3]
        
        dx = end["x"] - begin["x"]
        dy = end["y"] - begin["y"]
        length = math.sqrt(dx ** 2 + dy ** 2)
        
        if length == 0:
            continue
        
        t = (
            ((circle["position"]["x"] - begin["x"]) * dx + 
             (circle["position"]["y"] - begin["y"]) * dy) 
            / (length ** 2)
        )
        
        closest_x = begin["x"] + t * dx
        closest_y = begin["y"] + t * dy
        
        if not is_point_on_line_segment(closest_x, closest_y, begin, end):
            closest_x = begin["x"] if closest_x < begin["x"] else end["x"]
            closest_y = begin["y"] if closest_y < begin["y"] else end["y"]
        
        dx = closest_x - circle["position"]["x"]
        dy = closest_y - circle["position"]["y"]
        distance = math.sqrt(dx ** 2 + dy ** 2)
        
        if distance <= circle["radius"]:
            return True
    
    return False


def wrap_position(position: Dict, canvas_width: float = 1280, canvas_height: float = 720, radius: float = 0) -> Dict:
    x, y = position["x"], position["y"]
    
    if x + radius < 0:
        x = canvas_width + radius
    elif x - radius > canvas_width:
        x = -radius
    
    if y + radius < 0:
        y = canvas_height + radius
    elif y - radius > canvas_height:
        y = -radius
    
    return {"x": x, "y": y}