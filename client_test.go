// Copyright 2014 tsuru authors. All rights reserved.
// Use of this source code is governed by a BSD-style
// license that can be found in the LICENSE file.

package main

import (
	"encoding/json"
	"github.com/globocom/tsuru/app/bind"
	"launchpad.net/gocheck"
	"net/http"
	"net/http/httptest"
	"testing"
)

func Test(t *testing.T) { gocheck.TestingT(t) }

type S struct{}

var _ = gocheck.Suite(&S{})

func (s *S) TestGetEnvs(c *gocheck.C) {
	envs := map[string]bind.EnvVar{
		"DATABASE_HOST":     {Name: "DATABASE_HOST", Value: "localhost", Public: true},
		"DATABASE_USER":     {Name: "DATABASE_USER", Value: "root", Public: true},
		"DATABASE_PASSWORD": {Name: "DATABASE_PASSWORD", Value: "secret", Public: false},
	}
	data, err := json.Marshal(envs)
	c.Assert(err, gocheck.IsNil)
	var ok bool
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ok = r.URL.Path == "/envs"
		w.Write(data)
	}))
	defer ts.Close()
	client := &TsuruClient{URL: ts.URL}
	envs, err = client.GetEnvs("appname")
	c.Assert(err, gocheck.IsNil)
	c.Assert(ok, gocheck.Equals, true)
	c.Assert(envs, gocheck.NotNil)
}
