// Copyright 2013 tsuru authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package agent

import (
	"launchpad.net/gocheck"
	"testing"
)

func Test(t *testing.T) { gocheck.TestingT(t) }

type S struct{}

var _ = gocheck.Suite(&S{})

func (s *S) TestGetEnvs(c *gocheck.C) {
	client := &TsuruClient{}
	_, err := client.GetEnvs("appname")
	c.Assert(err, gocheck.IsNil)
}
