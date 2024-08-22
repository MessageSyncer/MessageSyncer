# Development Guide

## Adapter Template References:
- [Test Getter Template](https://github.com/MessageSyncer/TestGetter)
- [Test Pusher Template](https://github.com/MessageSyncer/TestPusher)

## Typesetting Guidelines

The basic message structure used in MessageSyncer is defined by the [`Struct`](./../src/model/struct.py) class. When developing a Getter, you can construct messages using the `Struct` class.

### Linebreak Rules for Struct Elements

| Context | `StructText` | `StructImage` |
|---------|--------------|---------------|
| Should the end of this element automatically wrap? | No | Yes |
| `Struct.__str__()` output | No | Yes |
| `Struct.asmarkdown()` output | No | Yes |

MessageSyncer recommends adhering to these linebreak rules during development of a Pusher.

### Recommended Message Structure

To maintain consistent message display, it is recommended that messages constructed by Getter developers follow this structure:

```
This is the title.

Content line 1.
Content line 2.
Content line n.

Author · Time · detail1 · detail2 · detailn
url
```

MessageSyncer provides a template to help achieve this format. You can use the `Struct.template1()` method to automatically generate a structured message. The function will handle linebreaks and formatting, so you do not need to manually insert line breaks in the content.

## API Documentation

For detailed API information, please refer to http://url.to.api/docs/