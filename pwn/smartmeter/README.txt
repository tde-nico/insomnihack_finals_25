If your host runs Ubuntu and want to use docker compose, you might need to modify the apparmor configuration:
```
sudo sysctl -w kernel.apparmor_restrict_unprivileged_unconfined=0
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0

docker compose build
docker compose up
```

See this github issue for details:
https://github.com/google/nsjail/issues/236#issuecomment-2267096267
