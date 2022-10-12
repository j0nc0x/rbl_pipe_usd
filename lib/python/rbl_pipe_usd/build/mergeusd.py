#!/usr/bin/env hython

"""Merge USD for different variants."""

import logging
import os

from rbl_pipe_core.util import filesystem

from rbl_pipe_sg import publish
from rbl_pipe_sg import template

from rbl_pipe_usd.build import sgconstructusd


logger = logging.getLogger(__name__)


class MergeUSD(sgconstructusd.SGConstructUSD):
    """Class to handle the merging of USD Steps."""

    def __init__(
        self,
        variant_name,
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
            merge_step(str): The USD step used merge and publish into.
            sg_template(str): The template to use when building the merged USD.
            sg_script(str): The SG script to use.
            sg_key(str): The SG key to use.
            asset_id(int): The asset ID to build the merged USD for.
            shot_id(int): The shot ID to build the merged USD for.
            project(str): The project to use when building the merged USD. If
                one isn't provided the value of RBL_PROJECT will be used.
        """
        super(MergeUSD, self).__init__(sg_script, sg_key, project=project)

        self.template = sg_template
        self.asset_id = asset_id
        self.shot_id = shot_id
        self.variant_name = variant_name
        self.merge_step = merge_step

        self.sg_script = sg_script
        self.sg_key = sg_key
        self.sg_template = template.SGTemplate(self.sg_script, self.sg_key)

    def _get_task_id(self, step, variant):
        """
        Get the task ID for the given step.

        Args:
            step(str): The step name to determine the task ID for.
            variant(str): The variant name to determine the task ID for.

        Returns:
            (int): The task ID.
        """
        task_name = self.__variant_task_name(step, variant)
        return self.sg_load.task_id_from_name(
            task_name,
            asset_id=self.asset_id,
            shot_id=self.shot_id,
        )

    def _get_merge_usd_task_id(self):
        """
        Get the task merge USD task ID.

        Returns:
            task_id(int): The merge USD task ID.

        Raises:
            RuntimeError: A task ID couldn't be generated.
        """
        task_id = self._get_task_id(self.merge_step, self.variant_name)
        if not task_id:
            raise RuntimeError(
                "Missing SG task. {variant}_{step} not found on SG for {asset}. Please "
                "notify production to get it amended.".format(
                    variant=self.variant_name,
                    step=self.merge_step,
                    asset=self.sg_load.asset_name_from_id(self.asset_id),
                )
            )
        return task_id

    def __variant_task_name(self, step, variant):
        """
        Generate a task name based on a step and variant.

        Args:
            step(str): The step to generate a task name based on.
            variant(str): The variant name to generate a task name based on.

        Returns:
            (str): The task name generated from the step and variant.
        """
        return "{variant}_{step}".format(
            variant=variant,
            step=step,
        )

    def usd_path(self, task_id):
        """
        Get the USD file path for the given task ID.

        Args:
            task_id(int): The SG task ID to look up.

        Returns:
            str: The USD filepath.
        """
        version = self.sg_template.current_version_from_template_list(
            [self.template],
            task_id,
        )
        if version:
            return self.sg_template.output_path_from_template(
                self.template,
                task_id,
                version,
            )
        return None

    def publish(self, flatten=False):
        """
        Publish the merged USD.

        Args:
            flatten(bool): Should we flatten the hierarchy during the publish process.

        Raises:
            RuntimeError: The publish failed.

        """
        publish_task = self._get_merge_usd_task_id()
        output_version = self.sg_template.next_version_from_template_list(
            [self.template],
            publish_task,
        )
        output_path = self.sg_template.output_path_from_template(
            self.template,
            publish_task,
            output_version,
        )

        filesystem.create_directory(os.path.dirname(output_path))

        try:
            self.write_usd(output_path, flatten=flatten)
            sg_publish = publish.SGPublish(
                self.sg_script,
                self.sg_key,
                task_id=publish_task,
                version=output_version,
                description="Asset / Shot USD Publisher",
            )
            sg_publish.add_main_publish_item(output_path, "USD Scene")
            result = sg_publish.run_publish()
        except Exception:
            raise RuntimeError("failed to publish")
        else:
            print(result)
