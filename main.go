// Copyright 2014 tsuru authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package agent

func main() {
	client := TsuruClient{URL: "localhost:8080"}
	envs, err := client.GetEnvs("myapp")
	if err != nil {
		panic(err)
	}
	err = SaveApprcFile(envs)
	if err != nil {
		panic(err)
	}
	err = ExecuteStartScript()
	if err != nil {
		panic(err)
	}
}
