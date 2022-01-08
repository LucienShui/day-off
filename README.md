# day-off

今天可以休息吗？

## API

| Url | Method | Description |
| --- | --- | --- |
| `/api/registre/<username>` | POST | 注册 |
| `/api/<username>/<date>` | GET | 查询某天是否休息 |
| `/api/<username>/<date>/<is-day-off>` | POST | 设置某天是否休息 |
