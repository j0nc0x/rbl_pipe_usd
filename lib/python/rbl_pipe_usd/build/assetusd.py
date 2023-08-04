#!/usr/bin/env hython

"""Construct Asset USD Files."""

import logging

from rbl_pipe_sg import load

from rbl_pipe_usd.build import mergeusdsteps
from rbl_pipe_usd.build import mergeusdvariants


logger = logging.getLogger(__name__)


class AssetUSD(mergeusdsteps.MergeUSDSteps):
    """Class to handle the construction of Asset USDs."""

    def __init__(
        self,
        asset_id,
        variant_name,
        sg_script,
        sg_key,
        template="usd_asset_publish",
        project=None,
        steps=None,
    ):
        """
        Initalise the asset usd builder.

        Args:
            asset_id(int): The asset ID to build the asset USD for.
            variant_name(str): The variant name to build the asset USD for.
            sg_script(str): The SG script to use.
            sg_key(str): The SG key to use.
            template(str): The template to use when building the asset USD.
            project(str): The project to use when building the asset USD. If one isn't
                provided the value of RBL_PROJECT will be used.
            steps(list): A list of short step name strings which will be used to
                construct the asset USD.
        """
        if steps is None:
            steps = [
                "MDL",
                "LAY",
                "FX",
                "LDV",
            ]

        super(AssetUSD, self).__init__(
            variant_name,
            steps,
            "ASS",
            template,
            sg_script,
            sg_key,
            asset_id=asset_id,
            project=project,
        )


class AssetMainUSD(mergeusdvariants.MergeUSDVariants):
    """Class to handle the construction of Asset Main USDs."""

    def __init__(
        self,
        asset_id,
        sg_script,
        sg_key,
        template="usd_asset_publish",
        project=None,
        variants=None,
    ):
        """
        Initalise the asset usd builder.

        Args:
            asset_id(int): The asset ID to build the asset USD for.
            sg_script(str): The SG script to use.
            sg_key(str): The SG key to use.
            template(str): The template to use when building the asset USD.
            project(str): The project to use when building the asset USD. If one isn't
                provided the value of RBL_PROJECT will be used.
            variants(list): A list of variant name strings which will be used to
                construct the asset variant USD.
        """
        self.sg_load = load.ShotgunLoad.get_instance(sg_script, sg_key)

        if variants is None:
            # Get all variants
            variants = self.get_all_variants(asset_id)

        super(AssetMainUSD, self).__init__(
            asset_id,
            variants,
            template,
            sg_script,
            sg_key,
            project=project,
        )

    def get_all_variants(self, asset_id):
        """
        Get all of the variants for the given asset ID.

        Args:
            asset_id(int): The asset ID to get the variants for.

        Returns:
            (list): A list of variant names.
        """
        step_id = self.sg_load.step_id_from_name("ASS", asset_id=asset_id)
        return [
            self.sg_load.variant_name_from_task(task.get("id"))
            for task in self.sg_load.get_asset_tasks(asset=asset_id, step=step_id)
            if not task.get("content").split("_")[0] == "main"
        ]


def publish_asset_usd(
    asset_id,
    variant_name,
    sg_script,
    sg_key,
    template="usd_asset_publish",
    project=None,
    steps=None,
    variants=None,
    force_publish=False,
):
    """
    Publish an asset USD based in the given inputs.

    Args:
        asset_id(int): The asset ID to build the asset USD for.
        variant_name(str): The variant name to build the asset USD for.
        sg_script(str): The SG script to use.
        sg_key(str): The SG key to use.
        template(str): The template to use when building the asset USD.
        project(str): The project to use when building the asset USD. If one isn't
            provided the value of RBL_PROJECT will be used.
        steps(list): A list of short step name strings which will be used to
            construct the asset USD.
        variants(list): A list of variant name strings which will be used to
            construct the asset main USD.
        force_publish(bool): Force the asset USD publish even if one already exists.

    Examples:
        Publish asset USD for an assset if one doesn't already exist.
        >>> from rbl_pipe_usd.build import assetusd
        >>> sg_script = "-"             # Use the appropriate SG script
        >>> sg_key = "-"                # Use the appropriate SG key
        >>> asset_id = 5633             # P3 - propTestoid
        >>> variant_name = "AvA"
        >>> assetusd.publish_asset_usd(asset_id, variant_name, sg_script, sg_key)
    """
    assetusd_builder = AssetUSD(
        asset_id,
        variant_name,
        sg_script,
        sg_key,
        template=template,
        project=project,
        steps=steps,
    )
    assetusd_builder.publish(force=force_publish)

    assetmainusd_builder = AssetMainUSD(
        asset_id,
        sg_script,
        sg_key,
        template=template,
        project=project,
        variants=variants,
    )
    assetmainusd_builder.publish(force=force_publish)
