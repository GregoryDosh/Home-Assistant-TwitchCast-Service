# Home-Assistant-TwitchCast-Service

# Installation/Usage

## Copy & Paste
Simply place the `twitchcast` folder in your `custom_components` folder in your Home Assistant config location and you should be able to use it in the example below.

## Git Clone
You can clone this repo into your `custom_components` folder in your Home Assistant config location with the name `twitchcast`.  The `.py` files at the root of the repo are symbolic links into the `twitchcast` folder.
```bash
git clone git@github.com:GregoryDosh/Home-Assistant-TwitchCast-Service.git twitchcast
```

## Git Submodule
Adding it as a submodule will allow you to pull updates in the future using `git submodule foreach git pull`.
```bash
git submodule add -b master git@github.com:GregoryDosh/Home-Assistant-TwitchCast-Service.git twitchcast
```


## Example Configuration
```yaml
twitchcast:
  chromecast_name: Living Room TV
  layout: right

```

## Services
### twitchcast.cast_stream
**channel**: Channel name
**layout** (optional): `left`, `right`, `top`, `bottom`

```json
{
    "channel": "monotonetim",
    "layout": "right"
}
```
