from .operations import *
import numpy as np

__all__ = ['Tensor']


class Tensor(object):
    """ A numpy.array-like object capable of serving as a node in a computational graph that
        supports back-propagation of derivatives via the chain rule."""
    __array_priority__ = 15.0

    def __init__(self, x, *, constant=False, _scalar_only=False, _creator=None):
        """ Parameters
            ----------
            x : array_like
                Input data, in any form that can be converted to an array.  This
                includes numbers, lists, lists of tuples, tuples, tuples of tuples, tuples
                of lists and ndarrays.

            Keyword-Only Arguments
            ----------------------
            constant : bool, optional (default=False)
                If True, this node is treated as a constant, and thus does not facilitate
                back propagation; `self.grad` will always return `None`.

            _scalar_only : bool, optional (default=False)
                Signals that self.backward() can only be invoked if self.ndim == 0.

            _creator: Optional[pygrad.Operation]
                The operation-instance whose forward pass produced `self`.
            """
        assert isinstance(constant, bool)
        self._scalar_only = _scalar_only
        self._creator = _creator

        if isinstance(x, Tensor):
            self.data = x.data
        else:
            self.data = np.asarray(x)
            self._check_valid_dtype(self.data.dtype)

        self.grad = None
        self._constant = constant

    @staticmethod
    def _check_valid_dtype(dtype):
        if not np.issubdtype(dtype, np.number):
            raise TypeError("Tensor data must be a numeric type")

    @classmethod
    def _op(cls, Op, *input_vars, op_args=None, op_kwargs=None):
        """ Wraps operations performed between tensors: f(a, b, ...).

            Parameters
            ----------
            Op : Operation
                Operation to be performed using `input_cars`.

            input_vars : Sequence[Union[Number, numpy.ndarray]]
                An arbitrary number of tensor-like objects, which are used as the input
                tensors to the forward-pass of the operation.

            *op_args
                Arbitrary positional arguments passed to the operation's forward pass.

            **op_kwargs
                Arbitrary keyword arguments passed to the operation's forward pass.

            Returns
            -------
            Tensor
                The tensor-result of the operation's forward-pass."""

        if op_args is None:
            op_args = tuple()

        if op_kwargs is None:
            op_kwargs = dict()

        tensor_vars = []
        for var in input_vars:
            if not isinstance(var, cls):
                var = cls(var, constant=True)
            tensor_vars.append(var)

        f = Op()
        op_out = f(*tensor_vars, *op_args, **op_kwargs)

        is_const = all(var.constant for var in tensor_vars)

        scalar_only = f.scalar_only and not is_const
        for var in tensor_vars:
            scalar_only = scalar_only or (var.scalar_only and not var.constant)

        return cls(op_out, constant=is_const, _creator=f, _scalar_only=scalar_only)

    def backward(self, grad=None):
        """ Compute set or accumulate `self.grad` with `grad`, and pass `self.creator.backward(grad)`.

            In effect, calling `self.backward()` will trigger a "back-propagation" from `self` through
            the preceding nodes in the computational graph. Thus a node, `a`, will have the attribute
            `self.grad` return the total derivative d(self)/da.

            Parameters
            ----------
            grad : Optional[float, array_like]
                The value of the incoming derivative. If self.grad is None, it is set to `grad`,
                otherwise its value is added with `grad`.

            Raises
            ------
            InvalidNonScalarBackprop
                The configuration of the computational graph is such that `self` must be a 0D tensor
                (i.e. scalar) to invoke self.backprop(grad)."""

        if grad is not None:
            grad = np.asarray(grad.data if isinstance(grad, Tensor) else grad)
        else:
            if self.ndim == 0:
                grad = np.asarray(1)
            else:
                grad = np.ones(self.shape, dtype=float)

        self.grad = np.asarray(grad if self.grad is None else self.grad + grad)

        if self._creator is not None:
            self._creator.backward(grad)


    def null_gradients(self):
        self.grad = None
        if self._creator is not None:
            self._creator.null_gradients()

    @property
    def scalar_only(self):
        """ Indicates whether or not `self.ndim` must be 0 in order to invoke `self.backprop()`.

            Returns
            -------
            bool"""
        return self._scalar_only

    @property
    def constant(self):
        """ A constant will not facilitate back-propagation at its node in the computational graph.

            Returns
            -------
            bool """
        return self._constant

    @property
    def creator(self):
        """ The `Operation` instance that produced `self`.

            Returns
            -------
            pygrad.Operation
            """
        return self._creator

    def __add__(self, other):
        return self._op(Add, self, other)

    def __radd__(self, other):
        return self._op(Add, other, self)

    def __sub__(self, other):
        # STUDENT CODE HERE
        pass
        return self._op(Subtract, self, other)

    def __rsub__(self, other):
        # STUDENT CODE HERE
        return self._op(Subtract, other, self)

    def __truediv__(self, other):
        return self._op(Divide, self, other)

    def __rtruediv__(self, other):
        return self._op(Divide, other, self)

    def __mul__(self, other):
        return self._op(Multiply, self, other)

    def __rmul__(self, other):
        return self._op(Multiply, other, self)

    def __neg__(self):
        return -1 * self

    def __repr__(self):
        if self.data.ndim == 0:
            return "Tensor({})".format(self.data.item())
        elif self.data.ndim == 1:
            return "Tensor({})".format(self.data)
        else:
            return "Tensor(\n{}\n)".format(self.data)

    def __lt__(self, value):
        if isinstance(value, Tensor):
            value = value.data
        return self.data < value

    def __le__(self, value):
        if isinstance(value, Tensor):
            value = value.data
        return self.data <= value

    def __gt__(self, value):
        if isinstance(value, Tensor):
            value = value.data
        return self.data > value

    def __ge__(self, value):
        if isinstance(value, Tensor):
            value = value.data
        return self.data >= value

    def __eq__(self, value):
        if isinstance(value, Tensor):
            value = value.data
        return self.data == value

    def __ne__(self, value):
        if isinstance(value, Tensor):
            value = value.data
        return self.data != value

    def __pos__(self):
        return self

    def __invert__(self):
        return -1 * self

    def __len__(self):
        return len(self.data)

    def __copy__(self):
        """ Produces a copy of self with copy.creator=None"""
        return Tensor(np.copy(self.data), _creator=None, constant=self.constant, _scalar_only=self.scalar_only)

    def __contains__(self, item):
        return self.data.__contains__(item)

    @property
    def size(self):
        return self.data.size

    @property
    def ndim(self):
        return self.data.ndim

    @property
    def dtype(self):
        return self.data.dtype

    @property
    def shape(self):
        return self.data.shape

    def sum(self, axis=None, keepdims=False):
        """ Sum of tensor elements over a given axis.

            Parameters
            ----------
            axis : Optional[int, Tuple[ints, ...]
                Axis or axes along which a sum is performed.  The default,
                axis=None, will sum all of the elements of the input tensor.  If
                axis is negative it counts from the last to the first axis.

                If axis is a tuple of ints, a sum is performed on all of the axes
                specified in the tuple instead of a single axis or all the axes as
                before.

            keepdims : bool, optional
                If this is set to True, the axes which are reduced are left
                in the result as dimensions with size one. With this option,
                the result will broadcast correctly against the input tensor.

            Returns
            -------
            sum_along_axis : Tensor
                A Tensor with the same shape as `self`, with the specified
                axis/axes removed. If `self` is a 0-d tensor, or if `axis` is None,
                a 0-dim Tensor is returned."""
        return self._op(Sum, self, op_args=(axis, keepdims))
