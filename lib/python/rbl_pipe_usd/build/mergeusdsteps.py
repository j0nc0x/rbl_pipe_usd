#!/usr/bin/env hython

"""Merge USD from different pipeline steps."""

import logging

from rbl_pipe_usd.build import mergeusd


logger = logging.getLogger(__name__)


class MergeUSDSteps(mergeusd.MergeUSD):
    """
    Class to handle the merging of USD Steps.

    Examples:
        Publish an asset USD.
        >>> from rbl_pipe_usd.build import mergeusd
        >>> sg_script = "-"             # Use the appropriate SG script
        >>> sg_key = "-"                # Use the appropriate SG key
        >>> asset_id = 5633             # P3 - propTestoid
        >>> variant_name = "AvA"
        >>> steps = ["MDL", "FX", "LDV"]
        >>> merge_step = "ASS"
        >>> sg_template = "usd_asset_publish"
        >>> m = mergeusd.MergeUSD(
                variant_name,
                steps,
                merge_step,
                sg_template,
                sg_script,
                sg_key,
                asset_id=asset_id,
            )
        >>> m.publish()

        Publish a shot USD.
        >>> from rbl_pipe_usd.build import mergeusd
        >>> sg_script = "-"             # Use the appropriate SG script
        >>> sg_key = "-"                # Use the appropriate SG key
        >>> shot_id = 4462              # P3 - 99_TST_80
        >>> variant_name = "main"
        >>> steps = ["BLD", "LAY", "ANM", "CFX", "FX", "LGT"]
        >>> merge_step = "SHT"
        >>> sg_template = "usd_shot_publish"
        >>> m = mergeusd.MergeUSD(
                variant_name,
                steps,
                merge_step,
                sg_template,
                sg_script,
                sg_key,
                shot_id=shot_id,
            )
        >>> m.publish()
    """

    def __init__(
        self,
        variant_name,
        steps,
        merge_step,
        sg_template,
        sg_script,
        sg_key,
        asset_id=None,
        shot_id=None,
        project=None,
    ):
        """
        Initalise the merged usd builder.

        Args:
            variant_name(str): The variant name to build the asset USD for.
            steps(list): A list of short step name strings which will be used to
                construct the asset USD.
            merge_step(str): The USD step used merge and publish into.
            sg_template(str): The template to use when building the merged USD.
            sg_script(str): The SG script to use.
            sg_key(str): The SG key to use.
            asset_id(int): The asset ID to build the merged USD for.
            shot_id(int): The shot ID to build the merged USD for.
            project(str): The project to use when building the merged USD. If
                one isn't provided the value of RBL_PROJECT will be used.

        variant_name,
        merge_step,
        sg_template,
        sg_script,
        sg_key,
        asset_id=None,
        shot_id=None,
        project=None,
        """
        super(MergeUSDSteps, self).__init__(
            variant_name,
            merge_step,
            sg_template,
            sg_script,
            sg_key,
            asset_id=asset_id,
            shot_id=shot_id,
            project=project,
        )
        self.steps = steps

        self.__add_sublayers()

    def __get_task_ids(self):
        """
        Generate a list of task IDs for the given variant.

        Returns:
            (list): A list of task IDs.
        """
        task_ids = []
        for step in self.steps:
            task_id = self._get_task_id(step, self.variant_name)
            if task_id:
                logger.debug(
                    "Task ID {task_id} found for {step}.".format(
                        task_id=task_id,
                        step=step,
                    )
                )
                task_ids.append(task_id)
            else:
                logger.warning(
                    "Task not created on SG, skipping: {step}".format(
                        step=step,
                    )
                )

        return task_ids

    def __add_sublayers(self):
        """Add sublayer references for the tasks from this asset."""
        for task_id in self.__get_task_ids():
            logger.info("Processing task: {task_id}".format(task_id=task_id))
            self.sublayer_by_taskid(task_id, self.template)

    def requires_publish(self):
        """
        Check if the merge USD requires publishing.

        Returns:
            bool: Does the merge USD require publishing.
        """
        task_id = self._get_merge_usd_task_id()

        requires_publish = False
        versions = self.sg_load.get_versions(
            task_id, published_file_type="USD Scene", force=True
        )
        if versions:
            logger.info(
                "Skipping Asset USD Publish that already exists for asset_id: "
                "{asset_id}".format(asset_id=self.asset_id)
            )
        else:
            requires_publish = True

        return requires_publish

    def publish(self, flatten=False, force=False):
        """
        Publish the merged USD steps.

        Args:
            flatten(bool): Should we flatten the hierarchy during the publish process.
            force(bool): Force the publish even if it isn't required.
        """
        if force or self.requires_publish():
            super(MergeUSDSteps, self).publish(flatten)
