"""
A python representation of edm object properties with associated useful functions.

Author: Oliver Copping
"""

from typing import Dict, ItemsView, KeysView, List, ValuesView

from .utils import get_colour_dict, get_properties_dict


class EdmProperties:
    """
    A python object storing the properties of an EdmObject.
    """

    def __init__(self, obj_type: str | None = None, defaults: bool = True) -> None:
        """
        Edm Object properties constructor.

        Args:
            defaults (bool, optional): Flag to use default values for Type.
                Defaults to True.
        """
        # initialise variables
        self.Type = obj_type
        self.Colour: Dict[str, str] = get_colour_dict()
        self._properties: Dict[str, str | bool | int | List[str] | Dict] = {}
        if defaults:
            self.setProperties()

    def setProperties(self) -> None:
        """
        Set EdmObject Properties.

        Attempt to populate self.Properties with default values and
        self.Colours with the index lookup table.

        Args:
            defaults (bool, optional): Flag to use default values for Type.
                Defaults to True.
        """
        default_dict: Dict[str, str | bool | int | List[str] | Dict]

        assert self.Type is not None

        PROPERTIES = get_properties_dict()

        if PROPERTIES:
            try:
                default_dict = PROPERTIES[self.Type]  # type: ignore
                self._properties.update(default_dict)
                return
            except Exception as e:
                pass

        # If PROPERTIES isn't defined, set some sensible values
        if self.Type != "Screen":
            self["object"] = "active" + self.Type.replace(" ", "") + "Class"
        self["major"], self["minor"], self["release"] = (4, 0, 0)
        self["x"], self["y"], self["w"], self["h"] = (0, 0, 100, 100)

    # def getProperty(self, property_key: str) -> str | bool | int | List[str] | Dict:
    def __getitem__(self, property_key: str) -> str | bool | int | List[str] | Dict:
        if property_key == "displayFileName" and property_key not in self._properties:
            return {0: ""}
        else:
            assert (
                property_key in self._properties
            ), f"---------------\n{self.Type}, '{property_key}'\n{self._properties}"
            return self._properties[property_key]

    # def setProperty(
    #     self, property_key: str, value: str | bool | int | List[str] | Dict
    # ) -> None:
    def __setitem__(
        self, property_key: str, value: str | bool | int | List[str] | Dict
    ) -> None:
        self._properties[property_key] = value

    def __delitem__(self, key: str) -> None:
        del self._properties[key]

    def __contains__(self, key: str) -> bool:
        return True if key in self._properties else False

    def __repr__(self) -> str:
        """Make "print self" produce a useful output."""
        output = str(self._properties)
        return output

    def items(
        self,
    ) -> ItemsView[str, str | bool | int | List[str] | Dict]:
        return self._properties.items()

    def keys(self) -> KeysView[str]:
        # assert self.Properties.keys().__class__ == {}.keys().__class__
        return self._properties.keys()

    def values(self) -> ValuesView[str | bool | int | List[str] | Dict]:
        # assert self.Properties.values().__class__ == {}.values().__class__
        return self._properties.values()

    def clear_properties(self) -> None:
        self._properties = {}
