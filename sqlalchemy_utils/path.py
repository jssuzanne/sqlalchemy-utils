from sqlalchemy.orm.attributes import InstrumentedAttribute


class Path(object):
    def __init__(self, path, separator='.'):
        if isinstance(path, Path):
            self.path = path.path
        else:
            self.path = path
        self.separator = separator

    def __iter__(self):
        for part in self.path.split(self.separator):
            yield part

    def __len__(self):
        return len(self.path.split(self.separator))

    def __repr__(self):
        return "%s('%s')" % (self.__class__.__name__, self.path)

    def __getitem__(self, slice):
        result = self.path.split(self.separator)[slice]
        if isinstance(result, list):
            return self.__class__(
                self.separator.join(result),
                separator=self.separator
            )
        return result

    def __eq__(self, other):
        return self.path == other.path and self.separator == other.separator

    def __ne__(self, other):
        return not (self == other)


def get_attr(mixed, attr):
    if isinstance(mixed, InstrumentedAttribute):
        return getattr(
            mixed.property.mapper.class_,
            attr
        )
    else:
        return getattr(mixed, attr)


class AttrPath(object):
    def __init__(self, class_, path):
        self.class_ = class_
        self.path = Path(path)
        self.parts = []
        last_attr = class_
        for value in self.path:
            last_attr = get_attr(last_attr, value)
            self.parts.append(last_attr)

    def __iter__(self):
        for part in self.parts:
            yield part

    def __invert__(self):
        def get_backref(part):
            prop = part.property
            backref = prop.backref
            if backref is None:
                raise Exception(
                    "Invert failed because property '%s' of class "
                    "%s has no backref." % (
                        prop.key,
                        prop.mapper.class_.__name__
                    )
                )
            return backref

        return self.__class__(
            self.parts[-1].mapper.class_,
            '.'.join(map(get_backref, reversed(self.parts)))
        )

    def __getitem__(self, slice):
        result = self.parts[slice]
        if isinstance(result, list):
            if result[0] is self.parts[0]:
                class_ = self.class_
            else:
                class_ = result[0].mapper.class_
            return self.__class__(
                class_,
                self.path[slice]
            )
        else:
            return result

    def __len__(self):
        return len(self.path)

    def __repr__(self):
        return "%s(%r, %r)" % (
            self.__class__.__name__,
            self.class_,
            self.path.path
        )

    def __eq__(self, other):
        return self.path == other.path and self.class_ == other.class_

    def __ne__(self, other):
        return not (self == other)
