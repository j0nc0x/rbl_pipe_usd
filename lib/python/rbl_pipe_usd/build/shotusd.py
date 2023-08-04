#!/usr/bin/env hython

"""Construct Shot USD Files."""

import logging

from rbl_pipe_usd.build import mergeusdsteps


logger = logging.getLogger(__name__)


class ShotUSD(mergeusdsteps.MergeUSDSteps):
    """Class to handle the construction of Shot USDs."""

    def __init__(
        self,
        shot_id,
        sg_script,
        sg_key,
        variant_name="main",
        template="usd_shot_publish",
        project=None,
        steps=None,
    ):
        """
        Initialise the shot USD builder.

        Args:
            shot_id(int): The shot ID to build the shot USD for.
            sg_script(str): The SG script to use.
            sg_key(str): The SG key to use.
            variant_name(str): The variant name to build the shot USD for.
            template(str): The template to use when building the shot USD.
            project(str): The project to use when building the shot USD. If one isn't
                provided the value of RBL_PROJECT will be used.
            steps(list): A list of short step name strings which will be used to
                construct the shot USD.
        """
        if steps is None:
            # What steps should we include?
            steps = [
                "BLD",
                "LAY",
                "ANM",
                "CFX",
                "FX",
                "LGT",
            ]

        super(ShotUSD, self).__init__(
            variant_name,
            steps,
            "SHT",
            template,
            sg_script,
            sg_key,
            shot_id=shot_id,
            project=project,
        )


def publish_shot_usd(
    shot_id,
    sg_script,
    sg_key,
    variant_name="main",
    template="usd_shot_publish",
    project=None,
    steps=None,
    force_publish=False,
):
    """
    Publish a shot USD based in the given inputs.

    Args:
        shot_id(int): The shot ID to build the shot USD for.
        sg_script(str): The SG script to use.
        sg_key(str): The SG key to use.
        variant_name(str): The variant name to build the shot USD for.
        template(str): The template to use when building the shot USD.
        project(str): The project to use when building the shot USD. If one isn't
            provided the value of RBL_PROJECT will be used.
        steps(list): A list of short step name strings which will be used to
            construct the shot USD.
        force_publish(bool): Force the asset USD publish even if one already exists.

    Examples:
        Publish shot USD for a shot if one doesn't already exist.
        >>> from rbl_pipe_usd.build import shotusd
        >>> sg_script = "-"     # Use the appropriate SG script
        >>> sg_key = "-"        # Use the appropriate SG key
        >>> shot_id = 4462      # P3 - 99_TST_80
        >>> shotusd.publish_shot_usd(shot_id, sg_script, sg_key)
    """
    shotusd_builder = ShotUSD(
        shot_id,
        sg_script,
        sg_key,
        variant_name=variant_name,
        template=template,
        project=project,
        steps=steps,
    )
    shotusd_builder.publish()
