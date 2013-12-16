// Copyright 2013 tsuru authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package agent

import (
	"github.com/globocom/tsuru/app/bind"
)

// Client represents a tsuru api client.
type Client interface {
	GetEnvs(app string) (map[string]bind.EnvVar, error)
}

type TsuruClient struct{}

func (*TsuruClient) GetEnvs(app string) (map[string]bind.EnvVar, error) {
	return nil, nil
}
