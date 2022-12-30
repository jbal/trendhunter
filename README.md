# Python TrendHunter API

## Overview
The TrendHunter API is a command line interface for scraping information
from the TrendHunter Ideas database.
- `trends`
- `lists`
- `categories`
- `search`

## Installation
**Optional** Create a dedicated directory, create an isolated
virtual environment, and activate the environment.
```
mkdir trendhunter && cd "$_"
python3 -m venv venv
source venv/bin/activate
```

Using `pip`, install the `trendhunter` library from the Python
Package Index,
```
pip install trendhunter
```

## Contributing
Before contributing, please install the `test` and `dev` versions of
the library,
```
pip install trendhunter[dev,test]
```

If you contribute and add tests to your contributions, you can run 
`./bin/test` from the root project directory. The script runs pytest
using the `/tests` directory as the root. It is not currently configured to accept
additional pytest options.

Once the package is ready to be uploaded, please complete the
following in order,
- Increment the `version` template in `pyproject.toml`
- Set the `PYPI_TOKEN` environment variable
- Run `/bin/twine`


## Usage
The API is implemented through Python Click, a command line
interface. The API implements 4 subcommands,
- `trends`
- `lists`
- `categories`
- `search`

Every command accepts a number of optional arguments, and one
required argument. The required argument is the name of the TrendHunter 
site from which you want to base your query. This argument is called the
`uid`, and must come after the subcommand.

The following excerpt is the Python Click help page for the `trends`
subcommand. Every subcommand is set up with the same options.
```
Usage: trendhunter trends [OPTIONS] UID

Options:
  -n INTEGER                      Number of articles. The API default is to
                                  return 50 articles matching the provided
                                  uid, but the `n` option is used to customize
                                  this value.  [default: 50]
  -k, --chunksize INTEGER         Size of a simultaneously-processed article
                                  chunk. The API default is to process 100
                                  articles at one time. Decrease this value to
                                  reduce memory usage.  [default: 100]
  -c, --concurrency INTEGER       Number of concurrent requests. The API
                                  default is to send 5 concurrent requests,
                                  but can be increased to 100. You may want to
                                  limit concurrency to avoid 429 errors on the
                                  TrendHunter API.  [default: 5]
  -y, --proxy TEXT                The HTTP url of a proxy server. The API
                                  default is to not use a proxy server, but if
                                  the TrendHunter API bans your IP address,
                                  you can provide one here. Please try to use
                                  a VPN before resorting to using a proxy
                                  server. If you do need to use a proxy,
                                  please be aware of the considerable risk if
                                  the provider is not secure.
  -t, --timeout INTEGER           Number of seconds until a request times out.
                                  The API default is to allow 10 seconds for a
                                  request to complete. If you are receiving
                                  several timeout exceptions, try to increaase
                                  this value.  [default: 10]
  -f, --format [0|1]              The output format. The API default (0) is to
                                  format the output to the console. If the
                                  user would prefer to output the details to a
                                  PowerPoint file, the 1 value can be used.
                                  [default: 0]
  -l, --loglevel [10|20|30|40|50]
                                  The log level of the root Python logger. The
                                  API default is to log anything at or above
                                  the INFO level. Decrease the value to view
                                  more verbose logs.  [default: 20]
  -p, --path PATH                 The path to write any output files. If one
                                  is not passed, the output path will be the
                                  current path.
  -x, --pixels <INTEGER INTEGER>...
                                  The maximum resolution of any created image
                                  files. The API default is to limit a
                                  thumbnail to a dimension of (300, 300). If
                                  an image is not equal in width and height
                                  dimension, the increase in resolution will
                                  be halted when the aspect ratio forces the
                                  larger dimension to hit the boundary
                                  specified here.  [default: 300, 300]
  --help                          Show this message and exit.
```

At any point, if you get stuck and would like to reference the
required and optional arguments, you can view the Click help page
for either the base `trendhunter` command or one of the subcommands,
```
trendhunter --help
```
```
trendhunter trends --help
```

## Examples
```
trendhunter trends holiday-giveaways
```
```
trendhunter lists 2023-tech-trends
```
```
trendhunter categories food
```
```
trendhunter search candy
```
