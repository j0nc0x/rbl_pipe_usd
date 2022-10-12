#!/usr/bin/env hython

"""Merge USD for different variants."""

import logging

from pxr import Usd

from rbl_pipe_usd.build import mergeusd


logger = logging.getLogger(__name__)


class MergeUSDVariants(mergeusd.MergeUSD):
    """
    Class to handle the merging of USD Variants.

    Examples:
        # Publish an asset USD.
        # >>> from rbl_pipe_usd.build import mergeusd
        # >>> sg_script = "-"             # Use the appropriate SG script
        # >>> sg_key = "-"                # Use the appropriate SG key
        # >>> asset_id = 5633             # P3 - propTestoid
        # >>> variant_name = "AvA"
        # >>> steps = ["MDL", "FX", "LDV"]
        # >>> merge_step = "ASS"
        # >>> sg_template = "usd_asset_publish"
        # >>> m = mergeusd.MergeUSD(
        #         variant_name,
        #         steps,
        #         merge_step,
        #         sg_template,
        #         sg_script,
        #         sg_key,
        #         asset_id=asset_id,
        #     )
        # >>> m.publish()

        # Publish a shot USD.
        # >>> from rbl_pipe_usd.build import mergeusd
        # >>> sg_script = "-"             # Use the appropriate SG script
        # >>> sg_key = "-"                # Use the appropriate SG key
        # >>> shot_id = 4462              # P3 - 99_TST_80
        # >>> variant_name = "main"
        # >>> steps = ["BLD", "LAY", "ANM", "CFX", "FX", "LGT"]
        # >>> merge_step = "SHT"
        # >>> sg_template = "usd_shot_publish"
        # >>> m = mergeusd.MergeUSD(
        #         variant_name,
        #         steps,
        #         merge_step,
        #         sg_template,
        #         sg_script,
        #         sg_key,
        #         shot_id=shot_id,
        #     )
        # >>> m.publish()
    """

    def __init__(
        self,
        asset_id,
        variants,
        sg_template,
        sg_script,
        sg_key,
        project=None,
    ):
        """
        Initalise the merged usd builder.

        Args:
            asset_id(int): The asset ID to build the merged USD for.
            variants(list): A list of variant names to construct the asset USD.
            sg_template(str): The template to use when building the merged USD.
            sg_script(str): The SG script to use.
            sg_key(str): The SG key to use.
            project(str): The project to use when building the merged USD. If
                one isn't provided the value of RBL_PROJECT will be used.
        """
        self.variants = variants
        self.step = "ASS"
        super(MergeUSDVariants, self).__init__(
            "main",
            "ASS",
            sg_template,
            sg_script,
            sg_key,
            asset_id=asset_id,
            project=project,
        )

        self.__add_variants()

    def usd_variant_name(self, asset_id, variant_name):
        """
        Generate the USD variant name to use.

        Args:
            asset_id(int): The asset ID to use.
            variant_name(str): The variant name to use when naming the USD variant.

        Returns:
            (str): The USD variant name.
        """
        return "{asset_name}{variant_name}".format(
            asset_name=self.sg_load.asset_name_from_id(asset_id),
            variant_name=variant_name,
        )

    def variant_name_from_usd_variant(self, usd_variant):
        """
        Get the variant name from the given USD variant.

        Args:
            usd_variant(str): The USD variant to extract the variant name from.

        Returns:
            str: The SG variant name.

        Raises:
            RuntimeError: Invalid USD variant name found.
        """
        asset_name = self.sg_load.asset_name_from_id(self.asset_id)
        if not usd_variant.startswith(asset_name):
            raise RuntimeError(
                "Invalid USD variant name: {variant}".format(variant=usd_variant)
            )
        return usd_variant.split(asset_name)[1]

    def get_variants_from_usd(self, variant_set="variant"):
        """
        Get all variants from the USD file.

        Args:
            variant_set(str): The name of the variant set to lookup.

        Returns:
            list: A list of SG variant names as looked up from the USD file.
        """
        task_id = self._get_merge_usd_task_id()
        # Load the usd
        usd_path = self.usd_path(task_id)
        if not usd_path:
            logger.debug(
                "No published USD could be found for task_id: {task_id}".format(
                    task_id=task_id,
                )
            )
            return []
        stage = Usd.Stage.Open(usd_path)
        logger.info("Opened {path}".format(path=usd_path))

        root_layer = stage.GetRootLayer()
        asset_reference = self.reference_name(
            self.asset_id,
            include_parent_transform=False,
        )
        asset_prim = root_layer.GetPrimAtPath(asset_reference)
        if not asset_prim:
            logger.warning(
                "Asset prim {reference} couldn't be found".format(
                    reference=asset_reference,
                )
            )
            return []

        usd_variants = asset_prim.GetVariantNames(variant_set)
        return [
            self.variant_name_from_usd_variant(variant)
            for variant
            in usd_variants
        ]

    def requires_publish(self):
        """
        Determine if the publish is required.

        Returns:
            bool: Publish is required.
        """
        usd_variants = self.get_variants_from_usd()
        logger.debug("SG Variants: {variants}".format(variants=self.variants))
        logger.debug("USD Variants: {variants}".format(variants=usd_variants))
        if sorted(self.variants) != sorted(usd_variants):
            logger.info(
                "Variants in .usd don't match asset system. Re-publish required."
                "Running Asset Main USD Publish for for asset_id: {asset_id}".format(
                    asset_id=self.asset_id,
                )
            )
            return True

        logger.debug(".usd up to date, no publish required.")
        return False

    def __get_task_ids(self):
        """
        Return a list of task IDs for the given variant.

        Returns:
            (list): A list of task IDs.
        """
        task_ids = []
        for variant in self.variants:
            task_id = self._get_task_id(self.step, variant)
            if task_id:
                logger.debug(
                    "Task ID {task_id} found for {variant}.".format(
                        task_id=task_id,
                        variant=variant,
                    )
                )
                task_ids.append(task_id)
            else:
                logger.warning(
                    "Task not created on SG, skipping: {variant}".format(
                        variant=variant,
                    )
                )

        return task_ids

    def __add_variants(self):
        """Add sublayer references for the tasks from this asset."""
        for task_id in self.__get_task_ids():
            logger.info("Processing task: {task_id}".format(task_id=task_id))
            variant = self.sg_load.variant_name_from_task(task_id)
            reference_name = self.reference_name(
                self.asset_id,
                include_parent_transform=False,
            )
            reference_primitive_path = self.reference_primitive_path(self.asset_id)
            variant_name = self.usd_variant_name(
                self.asset_id,
                variant,
            )
            self.reference_by_taskid(
                task_id,
                self.template,
                reference_name,
                reference_primitive_path,
                variant_name=variant_name,
                variant_set="variant",
            )

    def publish(self, flatten=False, force=False):
        """
        Publish the merged USD variants.

        Args:
            flatten(bool): Should we flatten the hierarchy during the publish process.
            force(bool): Force the publish even if it isn't required.
        """
        if force or self.requires_publish():
            super(MergeUSDVariants, self).publish(flatten)
