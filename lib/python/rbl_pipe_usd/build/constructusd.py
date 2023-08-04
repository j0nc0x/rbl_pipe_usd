#!/usr/bin/env hython

"""Construct USD Files."""

import logging
import os

from pxr import Tf
from pxr import Usd
from pxr import UsdGeom

logger = logging.getLogger(__name__)


class ConstructUSD(object):
    """Class to handle the construction of USD files."""

    def __init__(
        self,
    ):
        """Initialise the USD builder."""
        # Create a new stage to work in
        self.stage = Usd.Stage.CreateInMemory()
        self.sublayers = []
        self.references = []
        self.usd_variants = []
        logger.info("ConstructUSD Initialised.")

    def append_reference(
        self, name, path, primitive_path, variant_name=None, variant_set=None,
        over=False
    ):
        """
        Append a reference to the references list.

        Args:
            name(str): The name to use when creating the reference.
            path(str): The path to reference.
            primitive_path(str): The primitive path to reference from.
            variant_name(str): The USD variant name to use when referencing.
            variant_set(str): The USD variant set to create the reference within.
            over(bool): If True ``over`` is going to be used instead of ``def``
                (default).
        """
        logger.info(
            "Appending {name} | {path} | {primitive_path}".format(
                name=name,
                path=path,
                primitive_path=primitive_path,
            )
        )
        asset_reference = {}
        asset_reference["name"] = name
        asset_reference["path"] = path
        asset_reference["prim_path"] = primitive_path
        asset_reference["variant_name"] = variant_name
        asset_reference["variant_set"] = variant_set
        asset_reference["over"] = over
        self.references.append(asset_reference)

    def append_sublayer(self, path):
        """
        Append a sublayer to the sublayer list.

        Args:
            path(str): The path to reference.
        """
        self.sublayers.append(path)

    @staticmethod
    def get_default_prim(path):
        """
        Get the default prim for the given USD file.

        If we dont have the reference primitive path try and look it up, first trying
        the defaultPrim, thne falling back to traversing the scene graph.

        Args:
            path(str): The USD file to find the default prim for.

        Returns:
            prim(str): The default prim path for the given USD file.

        Raises:
            RuntimeError: The default prim path couldn't be determined.
        """
        try:
            stage = Usd.Stage.Open(path)
        except Tf.ErrorException:
            logger.warning("Could not open USD: {path}".format(path=path))
            return None

        prim = stage.GetDefaultPrim() or stage.GetPrimAtPath(
            stage.GetRootLayer().defaultPrim
        )

        # We should start setting the default prim so we don't have to do this
        if not prim:
            logger.warning("No default prim was set so having to guess.")
            root = stage.GetPrimAtPath("/")
            for child_prim in root.GetAllChildren():
                child_prim_path = child_prim.GetPath()
                if str(child_prim_path) != "/HoudiniLayerInfo":
                    return child_prim_path

            raise RuntimeError(
                "Could not work out the default prim for {path}".format(
                    path=path,
                )
            )

    def add_sublayer_to_stage(self, sublayer):
        """
        Create a sublayer in the USD scene graph.

        Args:
            sublayer(str): The sublayer to create a reference to.
        """
        logger.info(
            "Adding sublayer - {sublayer}".format(
                sublayer=sublayer,
            )
        )
        self.stage.GetRootLayer().subLayerPaths.append(sublayer)

    def add_reference_to_stage(
        self,
        name,
        path,
        prim_path=None,
        over=False,
        variant_name=None,
        variant_set=None,
    ):
        """
        Create a reference in the USD scene graph.

        Args:
            name(str): The name (ie. scene graph path) to create the reference at.
            path(str): The path to reference into the scene graph.
            prim_path(str): The primitive path to reference from.
            over(bool): By default a 'def' will be created. Use an over instead.
            variant_name(str): The variant name to use for this reference.
            variant_set(str): The variant set this should be added to.
        """
        logger.info(
            "Adding reference - {name}: {reference}".format(
                name=name,
                reference=path,
            )
        )
        if over:
            prim = self.stage.OverridePrim(name)
        else:
            UsdGeom.Xform.Define(self.stage, name)
            prim = self.stage.OverridePrim(name)

        if not prim_path:
            prim_path = self.get_default_prim(path)

        # Handle variants.
        if variant_name and variant_set:
            vsets = prim.GetVariantSets()
            # Add the variant set if it doesn't already exist.
            if vsets.HasVariantSet(variant_set):
                vset = vsets.GetVariantSet(variant_set)
            else:
                vset = vsets.AddVariantSet(variant_set)

            # Add the variant
            vset.AddVariant(variant_name)

            # Set the variant we are currently editing.
            vset.SetVariantSelection(variant_name)
            with vset.GetVariantEditContext():
                prim.GetReferences().AddReference(path, primPath=prim_path)
                self.usd_variants.append(variant_name)

            # Reset selection to first variant
            vset.SetVariantSelection(sorted(self.usd_variants)[0])

        # Proceed without variants.
        else:
            if variant_name or variant_set:
                logger.warning(
                    "variant_name and variant_set arguments must be used in "
                    "conjunction - skipping. (variant_set={variant_set}, "
                    "variant_name={variant_name})".format(
                        variant_set=variant_set,
                        variant_name=variant_name,
                    )
                )

            prim.GetReferences().AddReference(path, primPath=prim_path)

    def get_flattened_stage(self):
        """
        Return a flattened copy of the stage.

        Returns:
            stage(pxr.Usd.Stage): The flattened stage.
        """
        stage = self.stage.Flatten()
        return stage

    def __process_sublayers(self):
        """Process all the sublayers to be added to the USD scene graph."""
        for sublayer in self.sublayers:
            self.add_sublayer_to_stage(sublayer)

    def __process_references(self):
        """Process all the references to be added to the USD scene graph."""
        for ref in self.references:
            self.add_reference_to_stage(
                ref.get("name"),
                ref.get("path"),
                prim_path=ref.get("prim_path"),
                variant_name=ref.get("variant_name"),
                variant_set=ref.get("variant_set"),
                over=ref.get("over")
            )

    def write_usd(self, path, flatten=False):
        """
        Generate the USD scene graph and write it to the given file.

        Args:
            path(str): The file path to write the scene graph to. This should be either
                a .usd, .usda or .usdc.
            flatten(bool): Should we flatten the hierarchy during the export process.
        """
        self.__process_sublayers()
        self.__process_references()

        # Flatten the stage if we need to
        if flatten:
            out_stage = self.get_flattened_stage()
            logger.info("The USD stage was flattened.")
        else:
            out_stage = self.stage.GetRootLayer()

        out_stage.Export(path)

        # Due to a bug in USD we cant rely on the umask to result in the correct
        # permissions being set. See:
        # https://github.com/PixarAnimationStudios/USD/issues/1604
        os.chmod(path, 0o640)

        logger.info("USD file written to {path}".format(path=path))
