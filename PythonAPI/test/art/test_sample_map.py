# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

import carla
import pygame

import numpy as np

from carla import ColorConverter as cc
from . import SyncSmokeTest


class Camera(object):
    def __init__(self, sensor, size, record, output_path):
        self.sensor = sensor
        self.size = size
        self.recording = record
        self.image_ready = False
        self.output_path = output_path

        self.sensor.listen(lambda image: self.parse_image(image) )

    def get_transform_as_string(self):
        output = ""
        return output

    def parse_image(self, image):
        image.convert(cc.Raw)
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (self.size["height"], self.size["width"], 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        array = array.swapaxes(0, 1)

        surface = pygame.surfarray.make_surface(array)

        # surface = self.image_diff(surface)

        if self.recording:
            str_transform = self.get_transform_as_string(self.sensor.get_transform())
            image.save_to_disk('%s/%s' % self.output_path, str_transform)

        self.image_ready = True

    def destroy(self):
        self.sensor.destroy()

    """
    def image_diff(self, surface):
        img1_arr = pygame.PixelArray(self.prev_surface)
        img2_arr = pygame.PixelArray(surface)
        diff_arr = img2_arr.compare(img1_arr, distance=0.075)
        if not self.freeze_image_diff:
            self.prev_surface = surface

        return diff_arr.surface.copy()
        """


class TestSampleMap(SyncSmokeTest):
    self.cameras = []

    def test_sample_map(self):
        print("TestSampleMap")

        # get all available maps
        maps = self.client.get_available_maps()
        maps = ["Town03"]
        for m in maps:
            # load the map
            self.client.load_world(m)
            world = self.client.get_world()

            # get all spawn points
            spawn_points = self.world.get_map().get_spawn_points()

            # Apply sync mode
            self.settings = self.world.get_settings()
            settings = carla.WorldSettings(
                no_rendering_mode=False,
                synchronous_mode=True,
                fixed_delta_seconds=0.05)
            self.world.apply_settings(settings)

            # Spawn cameras
            image_size = {"width":640, "height":360}
            record_map = True
            output = "_out/" + m

            bp = world.get_blueprint_library().find('sensor.camera.rgb')
            bp.set_attribute('image_size_x', image_size["width"])
            bp.set_attribute('image_size_y', image_size["height"])

            self.cameras.append(Camera(
                world.spawn_actor(bp, carla.Transform(rotation = carla.Rotation(yaw = 0.0))),
                image_size,
                record_map
            ))
            self.cameras.append(Camera(
                world.spawn_actor(bp, carla.Transform(rotation = carla.Rotation(yaw = 90.0))),
                image_size,
                record_map
            ))
            self.cameras.append(Camera(
                world.spawn_actor(bp, carla.Transform(rotation = carla.Rotation(yaw = 180.0))),
                image_size,
                record_map
            ))
            self.cameras.append(Camera(
                world.spawn_actor(bp, carla.Transform(rotation = carla.Rotation(yaw = 270.0))),
                image_size,
                record_map
            ))

            world.tick()

            for spawn_point in spawn_points:

                # Reallocate cameras
                for camera in self.cameras:
                    camera.sensor.set_location(spawn_point)

                while not self.ready_for_tick():
                    # todo: check image diff
                    pass

                world.tick()

    def ready_for_tick(self):
        for camera in self.cameras:
            if not camera.image_ready:
                return False
        return True

