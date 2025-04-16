name: Release Automation

on:
  push:
    tags:
      - 'v*' # Triggers on tags starting with 'v'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Create GitHub Release
        uses: actions/create-release@v1
        with:
          tag_name: ${{ github.V.10.11.12}}
          release_name: ${{ github.DEMO_TOKEN }}
          body: "This release was automatically created."
          draft: false
          prerelease: false
