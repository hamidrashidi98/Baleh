from setuptools import setup, find_packages

setup(
    name="baleh",
    version="0.2.3",  # نسخه جدید
    packages=find_packages(include=["baleh", "baleh.*"]),
    include_package_data=True,
    package_data={
        "baleh": ["*.py"],
        "baleh.objects": ["*.py"],
        "baleh.utils": ["*.py"],
    },
    install_requires=[
        "aiohttp>=3.8.0",
        "Pillow>=9.0.0",
    ],
    author="Hamid Rashidi",
    author_email="spiderhamidman@gmail.com",
    description="A powerful Python library for developing Bale messenger bots",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/hamidrashidi98/baleh",
    license="MIT",  # اضافه کردن لایسنس
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Communications :: Chat",
    ],
    python_requires=">=3.7",
)