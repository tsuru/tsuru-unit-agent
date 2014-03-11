// Copyright 2014 tsuru authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package main

import "os"

func main() {
	target := os.Args[1]
	appName := os.Args[2]
	client := tsuruClient{URL: target}
	envs, err := client.getEnvs(appName)
	if err != nil {
		panic(err)
	}
	err = saveApprcFile(envs)
	if err != nil {
		panic(err)
	}
	err = executeStartScript()
	if err != nil {
		panic(err)
	}
}
