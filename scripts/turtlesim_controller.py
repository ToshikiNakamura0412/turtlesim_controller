#!/usr/bin/python3

from dataclasses import dataclass
import math
from typing import Optional

import rospy
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose

@dataclass(frozen=True)
class Param:
    num_of_sides: int
    length_of_side: float
    turn_direction_th: float

@dataclass
class Turtle:
    pose: Pose
    velocity: float
    yawrate: float

class TurtlesimController:
    def __init__(self) -> None:
        rospy.init_node("turtlesim_controller")

        self._param: Param = Param(
                rospy.get_param("~num_of_sides", 3),
                rospy.get_param("~length_of_side", 1.0),
                rospy.get_param("~turn_direction_th", 0.01),
                )
        self._turtle: Turtle = Turtle(
                None,
                rospy.get_param("~velocity", 0.5),
                rospy.get_param("~yawrate", 0.3)
                )

        self._prev_turn_pose: Optional[Pose] = None
        self._turn_count: int = 0

        self._cmd_vel_pub: rospy.Publisher = rospy.Publisher("/turtle1/cmd_vel", Twist, queue_size=1)
        self._pose_sub: rospy.Subscriber = rospy.Subscriber("/turtle1/pose", Pose, self._pose_callback, queue_size=1)

        rospy.loginfo("Node name: %s", rospy.get_name())
        rospy.loginfo("num_of_sides: %d", self._param.num_of_sides)
        rospy.loginfo("length_of_side: %s", self._param.length_of_side)
        rospy.loginfo("turn_direction_th: %s", self._param.turn_direction_th)
        rospy.loginfo("velocity: %s", self._turtle.velocity)
        rospy.loginfo("yawrate: %s", self._turtle.yawrate)

    def _pose_callback(self, msg: Pose) -> None:
        self._turtle.pose = msg
        self._set_cmd_vel()

    def _set_cmd_vel(self) -> None:
        cmd_vel: Twist = Twist()
        if not self._can_move():
            self._cmd_vel_pub.publish(cmd_vel)
            return None

        if self._prev_turn_pose is None:
            rospy.logwarn("prev_turn_pose is None")
            self._prev_turn_pose = self._turtle.pose
        distance: float = self._calc_distance(self._prev_turn_pose, self._turtle.pose)

        # go straight or turn
        if distance < self._param.length_of_side:
            rospy.loginfo("distance from last turning position: %f", self._param.length_of_side - distance)
            cmd_vel = self._get_cmd_vel_to_go_straight()
        else:
            if self._can_turn():
                rospy.loginfo("diff from target direction: %f", \
                    abs(self._calc_target_direction(self._turtle.pose, self._turn_count) - self._turtle.pose.theta))
                cmd_vel = self._get_cmd_vel_to_turn_in_place()
            else:
                self._turn_count += 1
                self._prev_turn_pose = None

        self._cmd_vel_pub.publish(cmd_vel)

    def _can_move(self) -> bool:
        return self._turn_count < self._param.num_of_sides

    def _calc_distance(self, pose1: Pose, pose2: Pose) -> float:
        return math.hypot(pose1.x - pose2.x, pose1.y - pose2.y)

    def _get_cmd_vel_to_go_straight(self) -> Twist:
        cmd_vel = Twist()
        cmd_vel.linear.x = self._turtle.velocity

        return cmd_vel

    def _get_cmd_vel_to_turn_in_place(self) -> Twist:
        cmd_vel = Twist()
        cmd_vel.angular.z = self._turtle.yawrate

        return cmd_vel

    def _can_turn(self) -> bool:
        return self._param.turn_direction_th < \
                abs(self._calc_target_direction(self._turtle.pose, self._turn_count) - self._turtle.pose.theta) and \
                self._turn_count < self._param.num_of_sides - 1

    def _calc_target_direction(self, pose: Pose, turn_count: int) -> float:
        target_direction_base: float = 2.0 * math.pi / self._param.num_of_sides;
        target_direction: float = target_direction_base * (self._turn_count + 1);
        while math.pi < target_direction:
            target_direction -= 2.0 * math.pi

        return target_direction

    def process(self) -> None:
        rospy.spin()
