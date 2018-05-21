# Install dependencies and libraries for Mask R-CNN
Especially for tensorflow, refer [here](https://hackernoon.com/running-yolo-on-odroid-yolodroid-5a89481ec141):

## Install JAVA:
Will install Java for bazel. It takes about 50MB.

```
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer -y
sudo apt-get install oracle-java8-unlimited-jce-policy

and 

sudo apt-get update
sudo apt-get install default-jre
sudo apt-get install default-jdk
sudo add-apt-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get install oracle-java8-installer
```

## Install Protobuf (For bazel build):
```
apt-get install curl
apt-get install automake
apt-get install libtool
git clone https://github.com/google/protobuf.git
cd protobuf
git checkout tags/v3.5.2
./autogen.sh
LDFLAGS=-static ./configure --prefix=$(pwd)/../
sed -i -e 's/LDFLAGS = -static/LDFLAGS = -all-static/' ./src/Makefile
make -j4
```

## Get some swap

Pop in a blank 8GB USB drive, which will get erased, and run ```sudo blkid```. Check the device name, usually /dev/sda1, and with that name, run if the name of the device is allocates as ```sda```:
```
sudo mkswap /dev/sda
sudo swapon /dev/sda
sudo swapon
```

## Install Bazel:

```
apt-get install unzip zip
wget --no-check-certificate https://github.com/bazelbuild/bazel/releases/download/0.11.1/bazel-0.11.1-dist.zip
unzip -q bazel-0.11.1-dist.zip -d bazel-0.11.1-dist
ulimit -c unlimited
# mkdir /tmp/bazel_tmp
# export TMPDIR=/tmp/bazel_tmp
cd bazel-0.11.1-dist
nano scripts/bootstrap/compile.sh
```
In ```nano scripts/bootstrap/compile.sh``` find line 117:
```
"run "${JAVAC}" -classpath "${classpath}" -sourcepath "${sourcepath}""
```
and add ```-J-Xms256m -J-Xmx384M``` as:
```
" run "${JAVAC}" -J-Xms256m -J-Xmx384m -classpath "${classpath}" -sourcepath "${sourcepath}""
```
In ```nano tools/cpp/lib_cc_configure.bzl``` find line 93:
```
def execute(repository_ctx, command, environment = None,
  """Execute a command, return stdout if succeed and throw an error if it fails. Doesn't %-escape the result!"""
```
and add ```return "arm"``` as:
```
def get_cpu_value(repository_ctx):
  return "arm"
```

And then,
```
./compile.sh
 sudo cp /root/bazel11/output/bazel /usr/local/bin/bazel
```
If tensorflow cannot find bazel excution file in ```/usr/bin/bazel```, then it will complain that it cannot find bazel so you need to install bazel.

## Install Tensorflow:
```
git clone --recurse-submodules https://github.com/tensorflow/tensorflow.git
cd tensorflow
grep -Rl 'lib64' | xargs sed -i 's/lib64/lib/g'
nano tensorflow/workspace.bzl
```
Replace the following
```
  native.new_http_archive(
      name = "eigen_archive",
      urls = [
          "http://mirror.bazel.build/bitbucket.org/eigen/eigen/get/f3a22f35b044.tar.gz",
          "https://bitbucket.org/eigen/eigen/get/f3a22f35b044.tar.gz",
      ],
      sha256 = "ca7beac153d4059c02c8fc59816c82d54ea47fe58365e8aded4082ded0b820c4",
      strip_prefix = "eigen-eigen-f3a22f35b044",
      build_file = str(Label("//third_party:eigen.BUILD")),
  )
```
with
```
  native.new_http_archive(
      name = "eigen_archive",
      urls = [
          "http://mirror.bazel.build/bitbucket.org/eigen/eigen/get/d781c1de9834.tar.gz",
          "https://bitbucket.org/eigen/eigen/get/d781c1de9834.tar.gz",
      ],
      sha256 = "a34b208da6ec18fa8da963369e166e4a368612c14d956dd2f9d7072904675d9b",
      strip_prefix = "eigen-eigen-d781c1de9834",
      build_file = str(Label("//third_party:eigen.BUILD")),
  )
```
And then,
```
./configure
```
**Configure the build:**
```
Extracting Bazel installation...
You have bazel 0.11.1- (@non-git) installed.
Please specify the location of python. [Default is /usr/bin/python]: /usr/lib/python3


/usr/lib/python3 is not executable.  Is it the python binary?
Please specify the location of python. [Default is /usr/bin/python]: /usr/bin/python3


Found possible Python library paths:
  /usr/lib/python3.5/dist-packages
  /usr/local/lib/python3.5/dist-packages
  /usr/lib/python3/dist-packages
Please input the desired Python library path to use.  Default is [/usr/lib/python3.5/dist-packages]

Do you wish to build TensorFlow with jemalloc as malloc support? [Y/n]: Y
jemalloc as malloc support will be enabled for TensorFlow.

Do you wish to build TensorFlow with Google Cloud Platform support? [Y/n]: n
No Google Cloud Platform support will be enabled for TensorFlow.

Do you wish to build TensorFlow with Hadoop File System support? [Y/n]: n
No Hadoop File System support will be enabled for TensorFlow.

Do you wish to build TensorFlow with Amazon S3 File System support? [Y/n]: n
No Amazon S3 File System support will be enabled for TensorFlow.

Do you wish to build TensorFlow with Apache Kafka Platform support? [y/N]: N
No Apache Kafka Platform support will be enabled for TensorFlow.

Do you wish to build TensorFlow with XLA JIT support? [y/N]: N
No XLA JIT support will be enabled for TensorFlow.

Do you wish to build TensorFlow with GDR support? [y/N]: N
No GDR support will be enabled for TensorFlow.

Do you wish to build TensorFlow with VERBS support? [y/N]: N
No VERBS support will be enabled for TensorFlow.

Do you wish to build TensorFlow with OpenCL SYCL support? [y/N]: N
No OpenCL SYCL support will be enabled for TensorFlow.

Do you wish to build TensorFlow with CUDA support? [y/N]: N
No CUDA support will be enabled for TensorFlow.

Do you wish to build TensorFlow with MPI support? [y/N]: N
No MPI support will be enabled for TensorFlow.

Please specify optimization flags to use during compilation when bazel option "--config=opt" is specified [Default is -march=native]: 


Would you like to interactively configure ./WORKSPACE for Android builds? [y/N]: N
Not configuring the WORKSPACE for Android builds.

Preconfigured Bazel build configs. You can use any of the below by adding "--config=<>" to your build command. See tools/bazel.rc for more details.
	--config=mkl         	# Build with MKL support.
	--config=monolithic  	# Config for mostly static monolithic build.
Configuration finished
```
And then build TensorFlow. Warning: This takes a really, really long time. Several hours.,
```
bazel build -c opt --copt="-funsafe-math-optimizations" --copt="-ftree-vectorize" --copt="-fomit-frame-pointer" --local_resources 8192,8.0,1.0 --verbose_failures tensorflow/tools/pip_package:build_pip_package

or

bazel build -c opt --copt="-mfpu=neon-vfpv4" --copt="-funsafe-math-optimizations" --copt="-ftree-vectorize" --copt="-fomit-frame-pointer" --local_resources 8192,8.0,1.0 --verbose_failures tensorflow/tools/pip_package:build_pip_package
```

Built! Now install it..
```
bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/tensorflow_pkg
sudo pip3 install /tmp/tensorflow_pkg/tensorflow-1.7.0-cp35-cp35m-linux_armv7l.whl --upgrade --ignore-installed
```

## Cleaning Up
There's one last bit of house-cleaning we need to do before we're done: remove the USB drive that we've been using as swap.
```
sudo swapoff /dev/sda
reboot
```
