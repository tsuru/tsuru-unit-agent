// Copyright 2013 tsuru authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package agent

import (
	"fmt"
	"github.com/globocom/tsuru/app/bind"
	ftesting "github.com/globocom/tsuru/fs/testing"
	"io/ioutil"
	"launchpad.net/gocheck"
)

func (s *S) TestSaveApprcFile(c *gocheck.C) {
	rfs := ftesting.RecordingFs{}
	old := fsystem
	fsystem = &rfs
	defer func() {
		fsystem = old
	}()
	envs := map[string]bind.EnvVar{
		"DATABASE_HOST":     {Name: "DATABASE_HOST", Value: "localhost", Public: true},
		"DATABASE_USER":     {Name: "DATABASE_USER", Value: "root", Public: true},
		"DATABASE_PASSWORD": {Name: "DATABASE_PASSWORD", Value: "secret", Public: false},
	}
	err := SaveApprcFile(envs)
	c.Assert(err, gocheck.IsNil)
	f, err := rfs.Open("/home/application/apprc")
	c.Assert(err, gocheck.IsNil)
	defer f.Close()
	_, err = ioutil.ReadAll(f)
	c.Assert(err, gocheck.IsNil)
}
