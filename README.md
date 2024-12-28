# lat-long-tz

Infers timezone from latitude and longitude geographical coordinates

```
Example: lat=39.9289, long=116.3883 -> Asia/Shanghai
```

Notable features:
- No internet connection required
- ~100K in size
- Any platform
- Any programming language
- Fast, can use hardware accelerators or GPU
- Usefully accurate

# Magic

This project **compresses** the tz geo database into machine learning (ML) model - the process called **training**. Released model is a set of floating point numbers, **parameters**, that any code can apply to a given lat-long pair to **infer** timezone. Of course the model has a decoder from a number to tz string built in as well.

The model is distributed in [Open Neural Network Exchange](https://onnx.ai/) format. Any [deployment scenario](https://onnx.ai/supported-tools.html#deployModel), including [runtimes](https://github.com/microsoft/onnxruntime) for many platforms and languages can be used for inference.

ML inference produces reasonably **accurate** results. Similar to lossy compression of the images, accuracy is less than 100% - this is a trade off between quality, speed, and size.

# Status

Experimental. Can current levels of accuracy and size be useful for any applications?

