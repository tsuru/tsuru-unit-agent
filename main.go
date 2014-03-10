// Copyright 2014 tsuru authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package main

func main() {
	client := tsuruClient{URL: "localhost:8080"}
	envs, err := client.getEnvs("myapp")
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
