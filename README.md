# pydf1

See src folder for usage instructions and license.

### Build and release
Make sure the `setup.py` file is up to date with at least the current version.

Then, in the `src` folder:

```
rm dist/*
python3 setup.py bdist_wheel
twine upload dist/*
```

the package `df1py3` can then be installed using `pip install df1py3`

### Known limitations
Although the current code is working and quite stable too, the implementation is incomplete:
- Ethernet and serial connection is supported but the code is modular and ready to accept a new PLC class that supports any other connection type.
- Some commands are not implemented, but the architecture is ready for more.
- Python 3.6 will work
