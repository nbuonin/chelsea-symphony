from wagtail.core import blocks


class YouTubeVideoBlock(blocks.StructBlock):
    youtube_id = blocks.CharBlock()

    class Meta:
        label = 'YouTube Embed'
        icon = 'media'
        template = 'main/blocks/youtube-video.html'
