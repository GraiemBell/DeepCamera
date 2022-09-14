"""Use SharpAI DeepCamera to perform intrusion detection."""
from __future__ import annotations

import io
import logging
import os
import sys
import time
import uuid
import voluptuous as vol
import requests

from homeassistant.components.image_processing import (
    CONF_CONFIDENCE,
    PLATFORM_SCHEMA,
    ImageProcessingEntity,
)

from homeassistant.const import (
    CONF_COVERS,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_SOURCE,
    CONF_TIMEOUT,
    CONF_URL,
)

from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.helpers import template
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util.pil import draw_box
from PIL import Image, ImageDraw, UnidentifiedImageError
_LOGGER = logging.getLogger(__name__)

ATTR_MATCHES = "matches"
ATTR_SUMMARY = "summary"
#ATTR_TOTAL_MATCHES = "total_matches"
ATTR_PROCESS_TIME = "process_time"

CONF_AUTH_KEY = "auth_key"
CONF_DETECTOR = "detector"
CONF_LABELS = "labels"
CONF_AREA = "area"
CONF_TOP = "top"
CONF_BOTTOM = "bottom"
CONF_RIGHT = "right"
CONF_LEFT = "left"
CONF_FILE_OUT = "file_out"

AREA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_BOTTOM, default=1): cv.small_float,
        vol.Optional(CONF_LEFT, default=0): cv.small_float,
        vol.Optional(CONF_RIGHT, default=1): cv.small_float,
        vol.Optional(CONF_TOP, default=0): cv.small_float,
        vol.Optional(CONF_COVERS, default=True): cv.boolean,
    }
)


LABEL_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_AREA): AREA_SCHEMA,
        vol.Optional(CONF_CONFIDENCE): vol.Range(min=0, max=100),
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        #vol.Required(CONF_URL): cv.string,
        #vol.Required(CONF_DETECTOR): cv.string,
        #vol.Required(CONF_TIMEOUT, default=90): cv.positive_int,
        #vol.Optional(CONF_AUTH_KEY, default=""): cv.string,
        #vol.Optional(CONF_FILE_OUT, default=[]): vol.All(cv.ensure_list, [cv.template]),
        #vol.Optional(CONF_CONFIDENCE, default=0.0): vol.Range(min=0, max=100),
        #vol.Optional(CONF_LABELS, default=[]): vol.All(
        #    cv.ensure_list, [vol.Any(cv.string, LABEL_SCHEMA)]
        #),
        #vol.Optional(CONF_AREA): AREA_SCHEMA,
    }
)

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Doods client."""
    # detector_name = config[CONF_DETECTOR]

    entities = []
    for camera in config[CONF_SOURCE]:
        entities.append(
            SharpAI(
                hass,
                camera[CONF_ENTITY_ID],
                camera.get(CONF_NAME),
                config,
            )
        )
        pass
    add_entities(entities)

class SharpAI(ImageProcessingEntity):
    """SharpAI image processing service client."""

    def __init__(self, hass, camera_entity, name, config):
        # """Initialize the DOODS entity."""
        self.hass = hass
        self._camera_entity = camera_entity
        if name:
            self._name = name
        else:
            name = split_entity_id(camera_entity)[1]
            self._camera_id = name
            self._name = f"SharpAI {name}"
        # self._doods = doods
        # self._file_out = config[CONF_FILE_OUT]
        # self._detector_name = detector["name"]

        # # detector config and aspect ratio
        # self._width = None
        # self._height = None
        # self._aspect = None
        # if detector["width"] and detector["height"]:
        #     self._width = detector["width"]
        #     self._height = detector["height"]
        #     self._aspect = self._width / self._height

        # # the base confidence
        # dconfig = {}
        # confidence = config[CONF_CONFIDENCE]

        # # handle labels and specific detection areas
        # labels = config[CONF_LABELS]
        # self._label_areas = {}
        # self._label_covers = {}
        # for label in labels:
        #     if isinstance(label, dict):
        #         label_name = label[CONF_NAME]
        #         if label_name not in detector["labels"] and label_name != "*":
        #             _LOGGER.warning("Detector does not support label %s", label_name)
        #             continue

        #         # If label confidence is not specified, use global confidence
        #         if not (label_confidence := label.get(CONF_CONFIDENCE)):
        #             label_confidence = confidence
        #         if label_name not in dconfig or dconfig[label_name] > label_confidence:
        #             dconfig[label_name] = label_confidence

        #         # Label area
        #         label_area = label.get(CONF_AREA)
        #         self._label_areas[label_name] = [0, 0, 1, 1]
        #         self._label_covers[label_name] = True
        #         if label_area:
        #             self._label_areas[label_name] = [
        #                 label_area[CONF_TOP],
        #                 label_area[CONF_LEFT],
        #                 label_area[CONF_BOTTOM],
        #                 label_area[CONF_RIGHT],
        #             ]
        #             self._label_covers[label_name] = label_area[CONF_COVERS]
        #     else:
        #         if label not in detector["labels"] and label != "*":
        #             _LOGGER.warning("Detector does not support label %s", label)
        #             continue
        #         self._label_areas[label] = [0, 0, 1, 1]
        #         self._label_covers[label] = True
        #         if label not in dconfig or dconfig[label] > confidence:
        #             dconfig[label] = confidence

        # if not dconfig:
        #     dconfig["*"] = confidence

        # # Handle global detection area
        # self._area = [0, 0, 1, 1]
        # self._covers = True
        # if area_config := config.get(CONF_AREA):
        #     self._area = [
        #         area_config[CONF_TOP],
        #         area_config[CONF_LEFT],
        #         area_config[CONF_BOTTOM],
        #         area_config[CONF_RIGHT],
        #     ]
        #     self._covers = area_config[CONF_COVERS]

        # template.attach(hass, self._file_out)

        # self._dconfig = dconfig
        # self._matches = {}
        # self._total_matches = 0
        # self._last_image = None
        # self._process_time = 0
        self._unknown_count = 0
        self._total_count = 0
        self._person_count = 0
        pass
    @property
    def unknown_count(self):
        """Return unknown count of detection result."""
        return self._unknown_count
    @property
    def total_count(self):
        """Return total person count of detection result."""
        return self._total_count
    @property
    def camera_entity(self):
        """Return camera entity id from process pictures."""
        return self._camera_entity

    @property
    def name(self):
        """Return the name of the image processor."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        #return self._total_matches
        return {'unknown':self._unknown_count,'total':self._total_count}

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        return {
            # ATTR_MATCHES: self._matches,
            # ATTR_SUMMARY: {
            #     label: len(values) for label, values in self._matches.items()
            # },
            # ATTR_TOTAL_MATCHES: self._total_matches,
            # ATTR_PROCESS_TIME: self._process_time,
        }

    def _save_image(self, image, matches, paths):
        # img = Image.open(io.BytesIO(bytearray(image))).convert("RGB")
        _LOGGER.info("Saving results image to path")
        # img_width, img_height = img.size
        # draw = ImageDraw.Draw(img)

        # # Draw custom global region/area
        # if self._area != [0, 0, 1, 1]:
        #     draw_box(
        #         draw, self._area, img_width, img_height, "Detection Area", (0, 255, 255)
        #     )

        # for label, values in matches.items():

        #     # Draw custom label regions/areas
        #     if label in self._label_areas and self._label_areas[label] != [0, 0, 1, 1]:
        #         box_label = f"{label.capitalize()} Detection Area"
        #         draw_box(
        #             draw,
        #             self._label_areas[label],
        #             img_width,
        #             img_height,
        #             box_label,
        #             (0, 255, 0),
        #         )

        #     # Draw detected objects
        #     for instance in values:
        #         box_label = f'{label} {instance["score"]:.1f}%'
        #         # Already scaled, use 1 for width and height
        #         draw_box(
        #             draw,
        #             instance["box"],
        #             img_width,
        #             img_height,
        #             box_label,
        #             (255, 255, 0),
        #         )

        # for path in paths:
        #     _LOGGER.info("Saving results image to %s", path)
        #     os.makedirs(os.path.dirname(path), exist_ok=True)
        #     img.save(path)
        pass

    def process_image(self, image):
        # """Process the image."""
        try:
            img = Image.open(io.BytesIO(bytearray(image))).convert("RGB")
            fileurl = r'/opt/nvr/detector/images/' +self._camera_id.replace(' ','_') + '_' + str(uuid.uuid4()) + r'.jpg'
            payloads = {'filename':fileurl,'camera_id':self._camera_id}
            img.save(fileurl)
            r = requests.post('http://localhost:3000/submit/image', json=payloads)
        except UnidentifiedImageError:
            _LOGGER.warning("Unable to process image, bad data")
            return
        except Exception as e:
            _LOGGER.error("Can't conver image to jpeg format")
            _LOGGER.error(e)
            return
        img_width, img_height = img.size
        _LOGGER.info(f"Processing Image wxh: {img_width}x{img_height}, response {r.json()}")
        
        if r.ok:
            response = r.json()

            self._unknown_count = response['unknown']
            self._total_count = response['total']
