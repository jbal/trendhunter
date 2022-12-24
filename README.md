# Python TrendHunter API

## Overview
The TrendHunter API is a command line interface for scraping information
from the TrendHunter Ideas database.
- `trends`
- `lists`
- `categories`
- `search`

## Installation
The library can be installed via the Python Package Index,
```
pip install trendhunter
```
**Note** the most recent version is `0.0.2`

## Usage
The API is implemented through Python Click, a command line
interface. The API supports 4 subcommands,
- `trends`
- `lists`
- `categories`
- `search`

Every command accepts a number of optional arguments, and one
required argument. The required argument is the name of the TrendHunter 
site from which you want to base your query. This argument is called the
`uid`, and must come after the subcommand.

The optional arguments are best described via an example. The following
excerpt is the Python Click help page for the `trends` subcommand.
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
  -p, --proxy TEXT                The HTTP url of a proxy server. The API
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
  -f, --format [0|1]              [default: 0]
  -l, --loglevel [10|20|30|40|50]
                                  [default: 20]
  -d, --directory DIRECTORY
  -x, --pixels <INTEGER INTEGER>...
  --help                          Show this message and exit.
```

At any point, if you get stuck and would like to reference the
required and optional arguments, you can view the Click help page
for either the base `trendhunter` command or one of the subcommands,
```
> trendhunter --help
```
```
> trendhunter trends --help
```

## Examples
```
> trendhunter trends holiday-giveaways
```
```
> trendhunter lists 2023-tech-trends
```
```
>trendhunter categories food
```
```
> trendhunter search candy
```
