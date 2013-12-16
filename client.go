// Copyright 2013 tsuru authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package agent

import (
	"encoding/json"
	"fmt"
	"github.com/globocom/tsuru/app/bind"
	"io/ioutil"
	"net/http"
)

// Client represents a tsuru api client.
type Client interface {
	GetEnvs(app string) (map[string]bind.EnvVar, error)
}

type TsuruClient struct {
	URL string
}

func (c *TsuruClient) GetEnvs(app string) (map[string]bind.EnvVar, error) {
	resp, err := http.Get(fmt.Sprintf("%s/envs", c.URL))
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	envs := map[string]bind.EnvVar{}
	err = json.Unmarshal(body, &envs)
	if err != nil {
		return nil, err
	}
	return envs, nil
}
